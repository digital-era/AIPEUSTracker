import yfinance as yf
import pandas as pd
import json
from datetime import datetime
import pytz

# --- 配置 ---

# 纳斯达克100成分股 (示例列表，实际使用时建议从可靠来源动态获取或定期更新)
# 为了简化，这里只列出一部分作为示例。请替换为完整的纳斯ДАК 100 列表。
NAS_TICKERS = [
    'AAPL', 'MSFT', 'AMZN', 'NVDA', 'GOOGL', 'GOOG', 'TSLA', 'META', 'AVGO', 'PEP',
    'COST', 'ADBE', 'CSCO', 'TMUS', 'NFLX', 'AMD', 'INTC', 'CMCSA', 'QCOM', 'INTU'
    # ... 添加更多股票代码
]

# 道琼斯30成分股
DOW_TICKERS = [
    'AXP', 'AMGN', 'AAPL', 'BA', 'CAT', 'CSCO', 'CVX', 'GS', 'HD', 'HON',
    'IBM', 'INTC', 'JNJ', 'KO', 'JPM', 'MCD', 'MMM', 'MRK', 'MSFT', 'NKE',
    'PG', 'TRV', 'UNH', 'CRM', 'VZ', 'V', 'WBA', 'WMT', 'DIS', 'DOW'
]

# 指数代码
INDEX_TICKERS = {
    "nasdaq": "^IXIC",
    "dowjones": "^DJI",
    "gold": "GC=F",      # COMEX Gold Futures
    "dollar": "DX-Y.NYB" # US Dollar Index
}

# 输出文件路径
OUTPUT_DIR = "data/"
NAS_OUTPUT_FILE = OUTPUT_DIR + "us_nas_stock_data.json"
DOW_OUTPUT_FILE = OUTPUT_DIR + "us_dowj_stock_data.json"
INDEX_OUTPUT_FILE = OUTPUT_DIR + "us_index_data.json"

# --- 函数定义 ---

def get_current_utc_time():
    """获取当前UTC时间并格式化"""
    return datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S UTC')

def generate_movers_json(tickers, filename):
    """获取股票列表的动态数据并生成Top/Down 20的JSON文件"""
    print(f"Fetching data for {len(tickers)} tickers for {filename}...")
    
    # 获取最近两天的数据以计算变化
    data = yf.download(tickers, period="2d", progress=False)
    if data.empty:
        print(f"Could not download data for {filename}.")
        return

    # 获取股票的详细信息（如名称）
    stock_info = {}
    for ticker in tickers:
        try:
            stock_info[ticker] = yf.Ticker(ticker).info.get('longName', ticker)
        except Exception as e:
            print(f"Could not get info for {ticker}: {e}")
            stock_info[ticker] = ticker

    # 计算百分比变化
    close_prices = data['Close']
    if len(close_prices) < 2:
        print("Not enough data to calculate change.")
        return
        
    prev_close = close_prices.iloc[-2]
    latest_close = close_prices.iloc[-1]
    
    percent_change = ((latest_close - prev_close) / prev_close) * 100
    
    results = []
    for ticker in tickers:
        if pd.notna(percent_change.get(ticker)):
            results.append({
                "代码": ticker,
                "名称": stock_info.get(ticker, ticker),
                "Percent": percent_change[ticker]
            })

    # 排序并获取Top/Down 20
    results.sort(key=lambda x: x['Percent'], reverse=True)
    top_up = results[:20]
    
    results.sort(key=lambda x: x['Percent'])
    top_down = results[:20]

    # 构建最终的JSON结构
    output_data = {
        "update_time_utc": get_current_utc_time(),
        "top_up_20": top_up,
        "top_down_20": top_down
    }

    # 保存到文件
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
    print(f"Successfully saved data to {filename}")

def generate_index_json(tickers, filename):
    """获取指数的1年历史数据并生成归一化的JSON文件"""
    print(f"Fetching 1-year index data for {filename}...")
    
    data = yf.download(list(tickers.values()), period="1y", interval="1d", progress=False)['Close']
    if data.empty:
        print(f"Could not download index data.")
        return
        
    # 归一化处理 (第一天 = 100)
    normalized_data = (data / data.iloc[0]) * 100
    
    output_data = {
        "update_time_utc": get_current_utc_time()
    }
    
    for key, ticker_symbol in tickers.items():
        series_data = []
        for date, value in normalized_data[ticker_symbol].items():
            if pd.notna(value):
                series_data.append({
                    "date": date.strftime('%Y-%m-%d'),
                    "value": value
                })
        output_data[key] = series_data

    # 保存到文件
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
    print(f"Successfully saved data to {filename}")


# --- 主程序 ---
if __name__ == "__main__":
    # 确保输出目录存在
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 生成股票动态数据
    generate_movers_json(NAS_TICKERS, NAS_OUTPUT_FILE)
    generate_movers_json(DOW_TICKERS, DOW_OUTPUT_FILE)
    
    # 生成指数历史数据
    generate_index_json(INDEX_TICKERS, INDEX_OUTPUT_FILE)
    
    print("\nAll data updated successfully!")
