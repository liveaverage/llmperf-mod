import os
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import re

def load_csv_files(directory):
    data = {}
    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            filepath = os.path.join(directory, filename)
            df = pd.read_csv(filepath, index_col=0)
            model_name = os.path.splitext(filename)[0]
            data[model_name] = df
    return data

def safe_filename(filename):
    return re.sub(r'[\\/:"*?<>|]+', '_', filename)

def plot_metrics(data, output_dir, metric_prefixes, better):
    metrics = data[list(data.keys())[0]].index
    concurrency = data[list(data.keys())[0]].loc['concurrency'].values.astype(float)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    grouped_metrics = {prefix: [] for prefix in metric_prefixes}
    for metric in metrics:
        if metric == 'concurrency':
            continue
        for prefix in metric_prefixes:
            if metric.startswith(prefix):
                grouped_metrics[prefix].append(metric)

    for prefix, metric_list in grouped_metrics.items():
        if not metric_list:
            continue
        plt.figure(figsize=(12, 6))
        for metric in metric_list:
            for model_name, df in data.items():
                plt.plot(concurrency, df.loc[metric].values, label=f'{model_name} - {metric}')
        
        plt.xlabel('Concurrency')
        plt.ylabel(prefix.replace('_', ' ').title())
        plt.title(f'{prefix.replace("_", " ").title()} vs Concurrency')
        plt.legend()
        plt.grid(True)

        safe_metric = safe_filename(prefix)
        output_path = os.path.join(output_dir, f'{safe_metric}.png')
        plt.savefig(output_path)
        plt.close()

def create_pdf(data, output_dir, pdf_path, metric_prefixes, better):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, "Benchmark Results", ln=True, align='C')
    pdf.ln(10)
    
    pdf.cell(200, 10, "Metrics Interpretation", ln=True, align='L')
    pdf.set_font("Arial", size=10)
    for prefix, value in better.items():
        pdf.cell(200, 10, f'{prefix.replace("_", " ").title()}: {value} is better', ln=True, align='L')
    pdf.ln(10)

    for prefix in metric_prefixes:
        safe_metric = safe_filename(prefix)
        plot_path = os.path.join(output_dir, f'{safe_metric}.png')
        if os.path.exists(plot_path):
            pdf.add_page()
            pdf.cell(200, 10, f'{prefix.replace("_", " ").title()} vs Concurrency', ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", size=10)
            pdf.cell(200, 10, f'{prefix.replace("_", " ").title()}: {better[prefix]} is better', ln=True, align='L')
            pdf.image(plot_path, x=10, y=40, w=pdf.w - 20)
            pdf.ln(95)

    summary = {}
    for prefix in metric_prefixes:
        summary[prefix] = {}
        for model, df in data.items():
            relevant_metrics = [metric for metric in df.index if metric.startswith(prefix)]
            if relevant_metrics:
                if better[prefix] == 'higher':
                    summary[prefix][model] = df.loc[relevant_metrics].max().max()
                else:
                    summary[prefix][model] = df.loc[relevant_metrics].min().min()
    
    top_models = {}
    for prefix in metric_prefixes:
        if better[prefix] == 'higher':
            top_models[prefix] = max(summary[prefix], key=summary[prefix].get)
        else:
            top_models[prefix] = min(summary[prefix], key=summary[prefix].get)
    
    pdf.add_page()
    pdf.cell(200, 10, "Summary Table", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=10)
    
    for prefix, model in top_models.items():
        pdf.cell(200, 10, f'Top Model for {prefix.replace("_", " ").title()}: {model}', ln=True, align='L')
    
    pdf.output(pdf_path)

directory = '/home/user/llmperf/scripts'  # Replace with the actual path
output_dir = 'output_plots'  # Directory where plots will be saved
pdf_path = 'benchmark_results.pdf'  # Output PDF file

metric_prefixes = ['requests_per_minute_(qpm)', 'throughput_token_per_s_(token/sec)', 
                   'time_to_first_token_in_ms_(ttft)', 'latency_ms_per_token_(inter_token_latency)']
better = {'requests_per_minute_(qpm)': 'higher', 
          'throughput_token_per_s_(token/sec)': 'higher',
          'time_to_first_token_in_ms_(ttft)': 'lower',
          'latency_ms_per_token_(inter_token_latency)': 'lower'}

data = load_csv_files(directory)
plot_metrics(data, output_dir, metric_prefixes, better)
create_pdf(data, output_dir, pdf_path, metric_prefixes, better)


