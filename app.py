import sys

import pandas as pd
from bokeh.embed import file_html
from bokeh.models import Range1d, LinearAxis
from bokeh.plotting import figure
from bokeh.resources import CDN
from flask import Flask, render_template, request
from pandas._testing import iloc
from pytrends.request import TrendReq
import yfinance as yf
import csv

app = Flask(__name__)

ticker_list = []
with open("tickers.csv", "r") as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # Skip the header row
    for row in reader:
        ticker_list.append(row[1])  # Add the ticker to the list


@app.route('/')
def index():
    # print('Hello world!', file=sys.stderr)
    return render_template('index.html', ticker_list=ticker_list)


@app.route('/graph', methods=['POST'])
def graph():
    print('Trying to graph', file=sys.stderr)
    # for key in request.form:
    #     print(f'{key}: {request.form[key]}', file=sys.stderr)
    # Get the user's input
    word = request.form['word']
    ticker = request.form['stock-ticker']
    start = request.form['timeframe-start']
    end = request.form['timeframe-end']

    # Get the data
    trend_data = get_trend_data(word, start + ' ' + end)
    stock_data = get_stock_data(ticker, start, end)

    html = graph_data(word, ticker, trend_data, stock_data)

    correlation = get_correlation(trend_data[word], stock_data['Close'])
    print(f'Correlation: {correlation}', file=sys.stderr)
    # embeds html in the template (graph.html)
    return render_template('index.html', plot_div=html, correlation=correlation)


def graph_data(word, ticker, trend_data, stock_data):
    print(f'Graphing data for {word} and {ticker}...', file=sys.stderr)
    # Create a plot (bokeh)
    bokeh_plot = figure(title=f'Popularity of the word "{word}" and {ticker} stock price over time',
                        x_axis_label='Date',
                        x_axis_type='datetime',
                        y_axis_label='Popularity')

    # Plot word popularity
    bokeh_plot.line(trend_data.index, trend_data[word], line_width=2, legend_label=word)
    bokeh_plot.y_range = Range1d(trend_data[word].min() - 1, trend_data[word].max() + 1)

    stock_range = "second y" + "_range"
    bokeh_plot.extra_y_ranges = {stock_range: Range1d(stock_data['Close'].min() - 1, stock_data['Close'].max() + 1)}

    # Plot stock price
    bokeh_plot.line(stock_data.index,
                    stock_data['Close'],
                    line_width=2, color='red',
                    legend_label=ticker,
                    y_range_name=stock_range)

    bokeh_plot.add_layout(LinearAxis(y_range_name=stock_range), "right")

    bokeh_plot.xaxis[0].ticker.desired_num_ticks = 10
    bokeh_plot.legend.location = 'top_left'
    bokeh_plot.legend.click_policy = 'hide'

    html = file_html(bokeh_plot, CDN, "my plot")
    return html


def get_trend_data(word, timeframe, geo=''):
    print(f'Getting data for {word} during {timeframe} at {geo}...', file=sys.stderr)
    # Authenticate and connect to the API
    pytr = TrendReq()
    # Get data from the API
    pytr.build_payload(kw_list=[word], timeframe=timeframe, geo=geo)
    data = pytr.interest_over_time()
    return data


def get_stock_data(ticker_name, start, end):
    print(f'Getting data for {ticker_name} from {start} to {end}...', file=sys.stderr)
    ticker = yf.Ticker(ticker_name)
    # Get data from the API
    data = ticker.history(start=start, end=end)
    return data


def get_correlation(word_data, stock_close_data):
    print(f'Getting correlation between\n{word_data}\nand\n{stock_close_data}\n...', file=sys.stderr)
    # convert stock_data from datetime64[ns, America/New_York] to datetime64[ns]
    stock_close_data.index = stock_close_data.index.tz_localize(None)
    net_data = pd.merge(word_data, stock_close_data, left_on='date', right_on='Date')
    # print("Printing net data", file=sys.stderr)
    # print(net_data, file=sys.stderr)
    correlation = net_data[word_data.name].corr(net_data['Close'])
    return correlation


def get_stocks_data(ticker_names, start, end):
    print(f'Getting data for {ticker_names} from {start} to {end}...', file=sys.stderr)
    tickers = yf.Tickers(ticker_names)  # ex: 'AAPL MSFT GOOG'
    stocks = tickers.history(start=start, end=end)
    return stocks


if __name__ == '__main__':
    app.run(debug=True)
