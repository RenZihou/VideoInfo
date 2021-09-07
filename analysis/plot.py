# -*- encoding: utf-8 -*-
# @Author: RZH

"""
do plots
"""

import sqlite3
from datetime import datetime

import numpy as np
import pandas as pd
import plotly as py
from plotly.subplots import make_subplots
import plotly.graph_objs as go

conn = sqlite3.connect('../data/data.sqlite3')


def plot_category():
    """
    plot popularity of different categories
    :return:
    """
    df = pd.read_sql_query('''SELECT play, coin, category
                           FROM videos
                           WHERE (category = 'MV') OR (category = 'VOCALOID·UTAU') 
                           OR (category = '原创音乐') OR (category = '翻唱')''', con=conn)
    df = df[df['play'] < 1_000_000][df['coin'] < 50_000]

    fig = make_subplots(rows=2, cols=2, column_widths=[0.6, 0.4],
                        specs=[[{'type': 'scatter', 'rowspan': 2}, {'type': 'bar'}],
                               [None, {'type': 'bar'}]])
    colors = ('#D12910', '#4F5EAA', '#15E2C5', '#F5C81B')
    categories = ('VOCALOID·UTAU', 'MV', '原创音乐', '翻唱')
    for color, category in zip(colors, categories):
        fig.add_trace(go.Scatter(x=df[df['category'] == category]['play'], y=df[df['category'] == category]['coin'],
                                 marker={'color': color, 'opacity': 0.5}, mode='markers', trendline='ols',
                                 name=category, xaxis='x1', yaxis='y1', legendgroup=category),
                      row=1, col=1)
        fig.add_trace(go.Bar(x=[df[df['category'] == category]['coin'].mean()], y=[category],
                             marker={'color': color}, orientation='h', name=category, showlegend=False,
                             xaxis='x2', yaxis='y2', text=[category], textposition='auto', legendgroup=category),
                      row=1, col=2)
        fig.add_trace(go.Bar(x=[df[df['category'] == category]['play'].mean()], y=[category],
                             marker={'color': color}, orientation='h', name=category, showlegend=False,
                             xaxis='x3', yaxis='y3', text=[category], textposition='auto', legendgroup=category),
                      row=2, col=2)

    fig.update_layout(height=700, width=1400,
                      title={'text': '<b>Popularity of Different Categories</b>', 'xanchor': 'center', 'x': 0.5},
                      legend={'x': 0.5, 'y': 1, 'xanchor': 'right'})
    fig['layout']['xaxis1'] = {'title': '<b>play</b>', 'domain': (0, 0.5)}
    fig['layout']['yaxis1'] = {'title': '<b>coin</b>'}
    fig['layout']['xaxis2'] = {'title': '<b>average coin</b>', 'domain': (0.6, 1), 'anchor': 'y2'}
    fig['layout']['yaxis2'] = {'title': '<b>category</b>', 'domain': (0, 0.45), 'anchor': 'x2', 'showticklabels': False}
    fig['layout']['xaxis3'] = {'title': '<b>average play</b>', 'domain': (0.6, 1), 'anchor': 'y3'}
    fig['layout']['yaxis3'] = {'title': '<b>category</b>', 'domain': (0.55, 1), 'anchor': 'x3', 'showticklabels': False}

    py.offline.plot(fig, filename='./output/01_category.html')
    return


def plot_duration():
    """
    plot popularity of variant durations
    :return:
    """
    df = pd.read_sql_query('''SELECT coin, duration, category
                           FROM videos
                           WHERE (category = 'MV') OR (category = 'VOCALOID·UTAU') 
                           OR (category = '原创音乐') OR (category = '翻唱')''', con=conn)
    df = df[df['duration'] < 600][df['coin'] < 50_000]  # less than 10 minutes
    bins = np.linspace(0, 600, 31)  # step: 20 sec
    hist = df.groupby([pd.cut(df['duration'], bins), 'category']).count().unstack()['coin']

    fig = make_subplots(specs=[[{'secondary_y': True}]])
    colors = ('#D12910', '#4F5EAA', '#15E2C5', '#F5C81B')
    categories = ('VOCALOID·UTAU', 'MV', '原创音乐', '翻唱')
    for color, category in zip(colors, categories):
        fig.add_trace(go.Scatter(x=df[df['category'] == category]['duration'], y=df[df['category'] == category]['coin'],
                                 marker={'color': color, 'opacity': 0.7}, mode='markers', legendgroup=category,
                                 name='coin', legendgrouptitle={'text': category}, xaxis='x1', yaxis='y1'),
                      secondary_y=False)
        fig.add_trace(go.Scatter(x=bins + 10, y=hist[category],
                                 line={'color': color, 'shape': 'spline'}, legendgroup=category, name='distribution',
                                 xaxis='x1', yaxis='y2'),
                      secondary_y=True)

    fig.update_layout(height=700, width=700,
                      title={'text': '<b>Popularity of Variant Durations</b>', 'xanchor': 'center', 'x': 0.5},
                      legend={'x': 1, 'y': 1, 'xanchor': 'right'})

    fig.update_xaxes(title_text='<b>duration</b>', domain=(0, 1))
    fig.update_yaxes(title_text='<b>coin</b>', secondary_y=False)
    fig.update_yaxes(title_text='<b>distribution</b>', showticklabels=False, showgrid=False, secondary_y=True)

    py.offline.plot(fig, filename='./output/02_duration.html')
    return


def plot_pub_time():
    """
    plot popularity of variant publish time
    :return:
    """

    df = pd.read_sql_query('''SELECT coin, category, pub_time
                           FROM videos
                           WHERE (category = 'MV') OR (category = 'VOCALOID·UTAU') 
                           OR (category = '原创音乐') OR (category = '翻唱')''', con=conn)
    df = df[df['coin'] < 50_000]
    df['weekday'] = df['pub_time'].apply(lambda x: datetime.fromtimestamp(x).strftime('%A'))
    df['hour'] = df['pub_time'].apply(lambda x: int(datetime.fromtimestamp(x).strftime('%H')))
    weekdays = ('Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')
    hours = ('midnight', 'dawn', 'morning', 'afternoon', 'evening', 'night')  # 0 4 8 12 16 20 24
    h_bins = np.linspace(0, 24, 7)  # step: 4 hr
    group_d = df.groupby(['weekday', 'category']).mean().unstack()['coin'].reindex(weekdays)
    group_h = df.groupby([pd.cut(df['hour'], h_bins), 'category']).mean().unstack()['coin']
    group_h.index = hours

    fig = make_subplots(cols=2, rows=1, specs=[[{'type': 'polar'}] * 2])
    colors = ('#D12910', '#4F5EAA', '#15E2C5', '#F5C81B')
    categories = ('VOCALOID·UTAU', 'MV', '原创音乐', '翻唱')
    for color, category in zip(colors, categories):
        fig.add_trace(go.Scatterpolar(theta=list(group_d.index) + [weekdays[0]],  # repeat first point to close the line
                                      r=list(group_d[category]) + [group_d[category][weekdays[0]]],
                                      line={'color': color, 'shape': 'spline'},
                                      legendgroup=category, name=category),
                      col=1, row=1)
        fig.add_trace(go.Scatterpolar(theta=list(group_h.index) + [hours[0]],
                                      r=list(group_h[category]) + [group_h[category][hours[0]]],
                                      line={'color': color, 'shape': 'spline'},
                                      legendgroup=category, name=category, showlegend=False),
                      col=2, row=1)

    fig.update_layout(height=700, width=1400,
                      title={'text': '<b>Popularity of Variant Publish Time</b>', 'xanchor': 'center', 'x': 0.5})

    py.offline.plot(fig, filename='./output/03_pub_time.html')
    return


if __name__ == '__main__':
    plot_category()
    plot_duration()
    plot_pub_time()
    pass
