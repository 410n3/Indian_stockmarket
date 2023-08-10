#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 10 17:40:44 2023

@author: maneeshradhakrishnan
"""

# streamlit_app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_option_menu import option_menu
import datetime


def calculate_ema(data, window):
    return data.ewm(span=window, adjust=False).mean()

def calculate_macd(data, short_window, long_window):
    short_ema = calculate_ema(data, short_window)
    long_ema = calculate_ema(data, long_window)
    macd = short_ema - long_ema
    signal = calculate_ema(macd, 9)
    return macd, signal

def plot_macd(macd, signal, hist):
    plt.figure(figsize=(12, 4))
    plt.plot(macd.index, macd, label='MACD', color = '#EBD2BE')
    plt.plot(macd.index, signal, label='Signal Line', color='#E5A4CB')
    plt.bar(macd.index, hist, label='Histogram', color=(hist > 0).map({True: '#2BA02B', False:'#D53E4F'}))
    plt.legend(loc='upper left')
    return plt

def analyze_macd(ticker):
    data = yf.download(ticker, start='2022-01-01')['Close']
    macd, signal = calculate_macd(data, 12, 26)
    hist = macd - signal

    close_to_intersection = (macd[-1] - signal[-1]) ** 2 < 0.1
    below_zero = macd[-1] < 0 and signal[-1] < 0

    if below_zero and close_to_intersection:
        st.warning(f"For {ticker}, both MACD and Signal lines are below zero and close to intersection. This might be a buy call.")
        
        st.pyplot(plot_macd(macd, signal, hist))
    else:
        st.toast(f"For {ticker}, conditions for a buy call are not met.",icon='😓')
        

def main():
    page_title="Indian stock buy sell helper"
    page_icon=":chart_with_downwards_trend:" 
    st.set_page_config(page_title=page_title,page_icon=page_icon)
    st.markdown(""" <style> #MainMenu {visibility: hidden;}footer {visibility: hidden;}</style> """, unsafe_allow_html=True)
    st.title(page_icon + " " + page_title)
    
    selected=option_menu( 
        menu_title=None,
        options=["For Buying","Interected one"],
        orientation="horizontal") 
    if selected=="For Buying":
        user = st.radio(
        "Do you want to use Default 200 top nifty stock list or you have your own ? ",
        ('Default', 'My own list'))
        if user == 'Default':
            stocks = pd.read_csv("ind_nifty200list.csv")
            
    
            progress_text = "Operation in progress. Please wait."
        else:
            st.write("Select your stock list file.")
            uploaded_file = st.file_uploader("Choose a file", type="csv")
            if uploaded_file is not None:
                stocks = pd.read_csv(uploaded_file)
        if st.button('Check Now'):
            
                with st.spinner(progress_text):
                    for symbol in stocks['Symbol']:
                        symbol =symbol + ".NS"
                        analyze_macd(symbol)
                st.write("Select your stock list file.")
                uploaded_file = st.file_uploader("Choose a file", type="csv")
                if uploaded_file is not None:
                    stocks = pd.read_csv(uploaded_file)
        
                    st.warning("Checking all stocks .")
                    progress_text = "Operation in progress. Please wait."
                    my_bar = st.progress(0, text=progress_text)
                    for symbol, percent_complete in zip(stocks['Symbol'], range(100)):
                            symbol = symbol + ".NS"
                            analyze_macd(symbol)
                            my_bar.progress(percent_complete + 1, text=progress_text)
    if selected=="Interected one":
        st.title("MACD Intersection Checker for Nifty200 stocks")
        interection_days = st.number_input("Enter number of intersection days:",1)
        end_date = st.date_input("Enter the end date:", datetime.date.today())
        redirect= st.radio("Do you want to link",("Yes","No"))


        

        def calculate_macd(df, short_window=12, long_window=26, signal_window=9):
            df['EMA_short'] = df['Close'].ewm(span=short_window, min_periods=1, adjust=False).mean()
            df['EMA_long'] = df['Close'].ewm(span=long_window, min_periods=1, adjust=False).mean()
            df['MACD'] = df['EMA_short'] - df['EMA_long']
            df['Signal_line'] = df['MACD'].ewm(span=signal_window, min_periods=1, adjust=False).mean()
            df.drop(['EMA_short', 'EMA_long'], axis=1, inplace=True)
            return df
        
        def check_macd_intersection(symbol,symbol1,interection_days,end_date=end_date, num_days=200):
            # Calculate the start date based on the end date and the number of days
            end_date = pd.to_datetime(end_date)
            start_date = end_date - datetime.timedelta(days=num_days)
            
            # Fetch historical stock data for daily prices
            stock_data = yf.download(symbol, start=start_date, end=end_date)
            
            # Calculate MACD indicator
            stock_data = calculate_macd(stock_data)
            
            # Check for intersections below zero within the last 3 days
            intersections = []
            for i in range(1, len(stock_data)):
                if stock_data['MACD'][i] > stock_data['Signal_line'][i] and stock_data['MACD'][i-1] <= stock_data['Signal_line'][i-1] and stock_data['Signal_line'][i] < 0:
                    intersection_date = stock_data.index[i].to_pydatetime()
                    days_since_intersection = (end_date - intersection_date).days
                    if days_since_intersection <= interection_days:
                        
                        intersections.append({
                            'Date': intersection_date,
                            'Open': stock_data['Open'][i],
                            'Close': stock_data['Close'][i]
                        })
                elif stock_data['MACD'][i] < stock_data['Signal_line'][i] and stock_data['MACD'][i-1] >= stock_data['Signal_line'][i-1] and stock_data['Signal_line'][i] < 0:
                    intersection_date = stock_data.index[i].to_pydatetime()
                    days_since_intersection = (end_date - intersection_date).days
                    if days_since_intersection <= 3:
                        intersections.append({
                            'Date': intersection_date,
                            'Open': stock_data['Open'][i],
                            'Close': stock_data['Close'][i]
                        })

            return intersections, stock_data

        
        
        
        stocks = pd.read_csv("ind_nifty200list.csv")
        
        if st.button('Check Now'):
            for symbol in stocks['Symbol']:
                symbol1 = symbol
                intersections, stock_data = check_macd_intersection(symbol + ".NS", symbol1, interection_days, end_date=end_date, num_days=200)
            
                if intersections:
                    if redirect=="y":
                        url =f"https://in.tradingview.com/chart/my9CG1Nl/?symbol=NSE%3A{symbol1}" 
                        st.write(url)
                    else:
                         st.toast("Done",icon= "✅")
    
                    st.write(f"There is an intersection for {symbol1}")
                    chart_data = pd.DataFrame({
                        'MACD': stock_data['MACD'],
                        'Signal Line': stock_data['Signal_line']
                    })
                    st.line_chart(chart_data)
                    for intersection in intersections:
                        st.write("Intersection Date:", intersection['Date'].strftime('%Y-%m-%d'))
                        st.write("Open Price:", intersection['Open'])
                        st.write("Close Price:", intersection['Close'])
                else:
                    st.toast(f"There is no intersection for {symbol1}",icon="😭")
            
                
            
                # Upload the CSV file
    
        
if __name__ == '__main__':
    main()
