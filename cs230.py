"""
Class: CS230--Section 1
Name: Edgar Campos
Description: CS230 Final
I pledge that I have completed the programming assignment
independently.
I have not copied the code from a student or any source.
I have not given my code to any student. 
"""

import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D 
from math import radians, sin, cos, sqrt, atan2
import pydeck as pdk

stationfile = "current_bluebikes_stations.csv"
tripfile = "201501-hubway-tripdata.csv"
bluebikesimage = "https://facilities.northeastern.edu/wp-content/uploads/2021/12/Bluebikes-Pic-4-1860x970.jpg"

def loaddata(file1,file2):
    for file in [file1,file2]:
        if 'station' in file:
            df1 = pd.read_csv(file,header=1)
        elif 'tripdata' in file:
            df2 = pd.read_csv(file)
        else:
            return
    return df1,df2

def cleanTrips(trips):
    
    toreplace = {'\\N' : np.nan}
    trips = trips.replace(toreplace)
    
    trips.dropna(inplace=True)
    trips = trips.astype({'birth year':'int64'})
    trips = trips.reset_index()
    
    trips['age'] = 2015 - trips['birth year']
    
    trips['distance (km)'] = trips.apply(lambda row: calcDistance(row['start station latitude'],
                                                                     row['start station longitude'],
                                                                     row['end station latitude'],
                                                                     row['end station longitude']), axis=1)
    trips['minutes'] = trips['tripduration'] / 60
    
    trips = trips.drop(columns=['index','start station id','end station id',
                               'bikeid','gender','birth year','tripduration'])
    
    return trips

def cleanStations(trips):
    
    start = trips[['start station name','start station latitude','start station longitude']].drop_duplicates()
    start['Station Name'] = start['start station name']
    start['Lat'] = start['start station latitude']
    start['Lon'] = start['start station longitude']
    start = start.drop(columns=['start station name','start station latitude','start station longitude'])
    
    
    end = trips[['end station name','end station latitude','end station longitude']].drop_duplicates()
    end['Station Name'] = end['end station name']
    end['Lat'] = end['end station latitude']
    end['Lon'] = end['end station longitude']
    end = end.drop(columns=['end station name','end station latitude','end station longitude'])

    df = pd.concat([start, end]).drop_duplicates().reset_index(drop=True)
    df = df.sort_values(by='Station Name').reset_index(drop=True)

    
    return df

def calcDistance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Radius of the Earth in kilometers (change this value if needed)
    R = 6371.0

    # Calculate the distance
    distance = R * c

    return distance

def displayStations(stations, route=None):
    st.subheader('Bike Stations Map') 
    centerlat = stations['Lat'].mean()
    centerlon = stations['Lon'].mean()
    
    stationlayer = pdk.Layer(
        "ScatterplotLayer",
        data=stations,
        get_position=["Lon", "Lat"],
        filled=True,
        get_radius=5,
        radius_scale=6,
        get_fill_color=[0, 0, 255, 255],
        pickable=True,
        auto_highlight=True,
        get_line_color=[0, 0, 0],
        picking_radius=10,
    )
    if route:
        routelayer = pdk.Layer(
            "LineLayer",
            data=route,
            get_source_position=['start lon','start lat'][0],
            get_target_position=['end lon','end lat'][0],
            get_color=[0, 0, 255, 255],
            pickable=True,
            auto_highlight=True,
            get_width=5,
            width_scale=5,
            picking_radius=10,
        )
    else:
        routeLayer= pdk.Layer()
    
    viewstate = pdk.ViewState(
        latitude=centerlat,
        longitude=centerlon,
        zoom=12,
        pitch=0
    )
    
    deck = pdk.Deck(
        layers=[stationlayer,route]  ,
        initial_view_state=viewstate,
        map_style="mapbox://styles/mapbox/light-v9"
    )
    st.pydeck_chart(deck)
    st.markdown('This map shows all the Blue Bike stations by January of 2015. There are a lot of stations scattered in Cambridge along the Charles River.')
    
    popstart = route['start station name'][0]
    popend = route['end station name'][0]
    st.markdown(f'\nThe most popular route for January 2015 was from {popstart} to {popend}')
    

def mostPopularRoute(trips,stations):
    
    route_counts = trips.groupby(['start station name', 'end station name']).size().reset_index(name='count')
    most_popular_route = route_counts.loc[route_counts['count'].idxmax()]
    most_popular_route = most_popular_route.reset_index()
    most_popular_route = most_popular_route.T
    most_popular_route = most_popular_route.reset_index(drop=True)
    
    popular = pd.DataFrame()
    popular['start station name'] = most_popular_route[0]
    popular['end station name'] = most_popular_route[1]
    popular = popular.drop(0)
    popular.reset_index(drop=True)
    
    start = popular['start station name'][1]
    end = popular['end station name'][1]
    
    popular = popular.merge(stations,left_on=['start station name'], right_on=['Station Name'])
    mapper = {'Lat':'start lat', 'Lon': 'start lon'}
    popular = popular.rename(columns = mapper)
    popular = popular.merge(stations,left_on=['end station name'], right_on=['Station Name'])
    mapper = {'Lat':'end lat', 'Lon': 'end lon'}
    popular = popular.rename(columns = mapper)
    todrop = ['Station Name_x','Station Name_y']
    popular = popular.drop(columns=todrop)
    
    return popular

def displayTypePies(trips):
    
    fig, axs= plt.subplots(3,1,figsize=(5,5))

    counts = trips.groupby(['usertype']).size().reset_index(name='count')
    usertype = trips[['usertype','minutes','distance (km)']].groupby(['usertype']).sum(numeric_only=True).reset_index()
    colors = ['#004c6d','#c1e7ff']

    axs[0].pie(usertype['minutes'], labels=counts['usertype'], autopct='%1.1f%%',
               startangle=90, colors=colors)
    axs[0].set_title('Distribution of Total Ride Time (in minutes) by User Type')

    axs[1].pie(usertype['distance (km)'], labels=counts['usertype'], autopct='%1.1f%%', startangle=90,colors=colors)
    axs[1].set_title('Distribution of Total Ride Distance (in km) by User Type') 

    axs[2].pie(counts['count'], labels=counts['usertype'], autopct='%1.1f%%', startangle=90,colors=colors)
    axs[2].set_title('Distribution of User Type')
    st.subheader('Difference Between One-Time Customers and Blue Bike Subscribers')
    st.markdown('Blue Bikes have two different pricing plans, the single trip (customers) and their membership plan. It would be interesting to look at if members make up a disproportionate amount of bike use. Similar to gym plans, bike members could make a smaller proportion of bike use, or members could be making the most of their money through putting their membership to good use.')
    st.pyplot(fig)
    st.markdown("These pie charts show that subscribers make up almost exactly proportionate amounts of bike use compared to how many subscribers there are.")
    
def displayDistancebyTimeScatter(trips):
    
    fig, ax = plt.subplots(figsize=(6,6))

    threshold = 40 # This subsets the data to trips less than 40 minutes long. 
                    # A few outlier (two+ hour long trips) mess up the scale of the graph
    data = trips[trips['minutes'] < threshold]
    colors = {'Customer': '#003f5c','Subscriber':'#665191'}
    ax.scatter(data['minutes'],data['distance (km)'],
          c=data['usertype'].map(colors))

    handles = [Line2D([0], [0], marker='o', color='w', markerfacecolor=v, label=k, markersize=8) for k, v in colors.items()]
    ax.legend(title='Key', handles=handles, bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.xlabel('Time (in minutes)')
    plt.ylabel('Distance Traveled (in km)')
    plt.title('Time Users Spend vs Distance Traveled By User Type')
    st.pyplot(fig)
    st.markdown("This scatterplot shows the amount of time users spend on a ride, along with how far they go. There is a general linear relationship, where the more time people spend on their trip, generally they travel a farther difference. Showing the difference between subscribers and customers, there is no clear difference between the two, suggesting that both types of users are similarly in a rush.")

    
def displayCommonHourHist(trips):
    df = pd.DataFrame()
    df[['date', 'time']] = trips['starttime'].str.split(pat=' ', n=1, expand=True)
    df[['hour','minute','second']] = df['time'].str.split(pat=':', n=4, expand=True)
    df['usertype'] = trips['usertype']
    df = df.sort_values(by=['hour'])
    plt.figure(figsize=(10, 6))

    # Plot a histogram of bike trips by hour
    plt.hist(df['hour'],bins=24,color='#004c6d',edgecolor='black',alpha=0.7)
    plt.title('Most Common Time for Bike Trips')
    plt.xlabel('Hour of the Day')
    plt.ylabel('Number of Bike Trips')
    plt.xticks(range(24))

    # Show the most common hour
    commonhour = df['hour'].mode().values[0]
    plt.axvline(commonhour, color='black', linestyle='dashed', linewidth=2, label=f'Most Common Hour: {commonhour}')

    plt.legend()
    st.subheader('Most Popular Times for Blue Bike Users')
    st.pyplot(plt.gcf())
    st.markdown('This plot shows the distribution of Blue Bike use by hour of the day. During the month of January, 2015, 8am was the most common time for people to use Blue Bikes. There\'s another peak at 5pm. ')
    
    plt.clf()
    sub = df[df['usertype']=='Subscriber']
    plt.hist(sub['hour'],bins=24,color='#58508d',edgecolor='black',alpha=0.7)
    plt.title('Most Common Time for Bike Trips (Subscribers)')
    plt.xlabel('Hour of the Day')
    plt.ylabel('Number of Bike Trips')
    plt.xticks(range(24))
    commonhour = sub['hour'].mode().values[0]
    plt.axvline(commonhour, color='black', linestyle='dashed', linewidth=2, label=f'Most Common Hour: {commonhour}')
    st.pyplot(plt.gcf())
    st.markdown('This histogram shows the distribution of Blue Bike use by hour of the day for subscribers. During the month of January, 2015, 5pm was the most common time for people to use Blue Bikes, with a close peak at 8am too. This likely suggests that people who subscribe to Blue Bikes are mostly commuters.')
    plt.clf()
    
    cus = df[df['usertype']=='Customer']
    plt.hist(cus['hour'],bins=24,color='#a05195',edgecolor='black',alpha=0.7)
    plt.title('Most Common Time for Bike Trips (One-Time Customers)')
    plt.xlabel('Hour of the Day')
    plt.ylabel('Number of Bike Trips')
    plt.xticks(range(24))
    commonhour = cus['hour'].mode().values[0]
    plt.axvline(commonhour, color='black', linestyle='dashed', linewidth=2, label=f'Most Common Hour: {commonhour}')
    st.pyplot(plt.gcf())
    st.markdown('This histogram shows the distribution of Blue Bike use by hour of the day for subscribers. During the month of January, 2015, 8am was the most common time for people to use Blue Bikes. It\'s interesting that there were no customer trips at 11am at all in the data.')
    plt.clf()
   
    df['date'] = pd.to_datetime(df['date'])
    df['dayoftheweek'] = df['date'].dt.day_name()
    df = df.sort_values(by=['hour'])

    daysoftheweek = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    st.subheader('Most Popular Days for Blue Bike Users')
    day = st.selectbox('Select Day of the Week',sorted(daysoftheweek))
    daybeforeindex = daysoftheweek.index(day) - 1
    daybefore = daysoftheweek[daybeforeindex]

    if day != daysoftheweek[6]:
        dayafterindex = daysoftheweek.index(day) + 1
    else:
        dayafterindex = 0

    dayafter = daysoftheweek[dayafterindex]
    df2 = df[df['dayoftheweek'].isin([daybefore,day,dayafter])]

    plt.hist(df2['dayoftheweek'],bins=3,color='#003f5c',edgecolor='black',alpha=0.7)
    plt.title('Most Common Day for Bike Trips')
    plt.xlabel('Day of the Week')
    plt.ylabel('Number of Bike Trips')
    commonday = df2['dayoftheweek'].mode().values[0]
    plt.axvline(commonday, color='black', linestyle='dashed', linewidth=2, label=f'Most Common Day: {commonday}')
    plt.legend()
    
    
    st.pyplot(plt.gcf())
    popularday = df['dayoftheweek'].mode().values[0]
    st.markdown(f'The most popular day of the week for users to bike was {popularday}')
def main():
    stationdata,tripdata = loaddata(tripfile,stationfile)
    tripdata = cleanTrips(tripdata)
    stationdata = cleanStations(tripdata)
    
    st.set_page_config(page_title="Boston Bluebike Trips", initial_sidebar_state="expanded" )
    page = st.sidebar.selectbox("Select a page", ["Home", "Stations Map", "Popular Times",
                                                  "Membership"])
    
    if page == "Home":
        st.markdown("<h1 style='text-align: center;'>Boston Bluebike Insight</h1>",
                    unsafe_allow_html=True) 
        st.markdown( "<h2 style='text-align: center;'>This app provides users with various tools to explore and analyze patterns within Boston Blue Bike data.</h2>", unsafe_allow_html=True) 
        st.image(bluebikesimage) 
        st.markdown('The Boston Bluebikes is a bike sharing program for Metro Boston, offering affordable and convenient transportation for quick trips around town.')
    elif page == "Stations Map":
        popularRoute = mostPopularRoute(tripdata,stationdata)
        displayStations(stationdata, route=popularRoute)
    elif page == "Popular Times": 
        displayCommonHourHist(tripdata) 
    elif page == "Membership":
        displayTypePies(tripdata)
        displayDistancebyTimeScatter(tripdata)
    
    
    
if __name__ == "__main__":
    main()
