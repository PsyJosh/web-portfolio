### Functions List ###




## Necessary Packages ##
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from plotly import express as px
from plotly.io import write_html
import plotly.io as pio
import sqlite3
from sklearn.linear_model import LinearRegression
conn = sqlite3.connect("noaa.db")


## Prepare DataFrame function ##
def prepare_df(df):
    """
    The prepare_df() function reformats a DataFrame into a more
    helpful format for us to compute with, such as unit adjusting
    and title setting.
    Output: DataFrame. Adjusted columns and data.
    --
    Parameters: 
    - df: DataFrame. Unadjusted columns and data.
    """
    df = df.set_index(keys=["ID", "Year"])
    df = df.stack()
    df = df.reset_index()
    df = df.rename(columns = {"level_2"  : "Month" , 0 : "Temp"})
    df["Month"] = df["Month"].str[5:].astype(int)
    df["Temp"]  = df["Temp"] / 100
    return(df)


## Query Climate Database Function ##
def query_climate_database(country, year_begin, year_end, month):
    """
    The query_climate_database() function creates a DataFrame based on
    imported data. 
    Output: DataFrame. Only includes the data desired from specified
    parameters.
    -- 
    Parameters: 
    - country: str. Name of a country.
    - year_begin: int. The starting year of range.
    - year_end: int. The ending year of range.
    - month: int. Selected month. Acceptable values: 1-12.
    """
    ## Opening SQL Connection ##
    conn = sqlite3.connect("noaa.db")
    
    ## Finding country from string ##
    # SQL commands.
    cmd = \
    f"""
    SELECT C.[fips 10-4]
    FROM countries C
    WHERE C.name="{country}"
    """
    country_id_find = pd.read_sql_query(cmd, conn)
    country_id = country_id_find["FIPS 10-4"][0]
    
    # Setting up dataframe for query_climate_database #
    # SQL commands.
    cmd = \
    f"""
    SELECT S.name, S.latitude, S.longitude, T.id, T.year, T.month, T.temp
    FROM temperatures T
    LEFT JOIN stations S ON T.id = S.id
    WHERE SUBSTRING(T.id,1,2) = "{country_id}" 
    AND T.year<{year_end} 
    AND T.year>{year_begin} 
    AND T.month={month}
    """
    query_df = pd.read_sql_query(cmd, conn)
    
    # Including country column #
    query_df["Country"] = [country for i in range(len(query_df["Year"]))]
    
    ## Closing SQL Connection ##
    conn.close()
    
    return query_df
    

## Linear Regression on Climate Data Function ##
def climate_regression(data_group):
    """
    The climate_regression() function converts a set of datapoints
    and applies a linear regression to the data associated to 
    a given station.
    Output: Linear regression coefficient.
    --
    Parameters:
    - data_group: DataFrame. Set of data to apply a linear regression
    model on. 
    """
    # Year data.
    x = data_group[["Year"]] # 2 brackets because X should be a df
    # Temperature data to apply a linear regression.
    y = data_group["Temp"]   # 1 bracket because y should be a series
    LR = LinearRegression()
    LR.fit(x, y)
    return LR.coef_[0]


## Temperature Coefficient Plot Function ##
def temperature_coefficient_plot(country, year_begin, year_end, month, min_obs, **kwargs):
    """
    The temperature_coefficient_plot() function inputs a series of
    parameters and calls to the query_climate_database() and
    climate_regression() functions. The data is adjusted and plotted
    using Plotly Express and visualized. 
    Output: Plotly Express Geovisualization Plot
    --
    Parameters: 
    - country: str. Name of a country.
    - year_begin: int. The starting year of range.
    - year_end: int. The ending year of range.
    - month: int. Selected month. Acceptable values: 1-12.
    - min_obs: int. The minimum amount of observations a station
    must have in order to be plotted.
    - **kwargs allows passing of px.scatter_mapbox() arguments.
    """
    ## Pulling Dataset ##
    country_climate_data = query_climate_database(country,year_begin,year_end,month)
    
    ## Filtering Data by 'min_obs' ##
    for station in country_climate_data["NAME"].unique():
        if (country_climate_data["NAME"]==station).sum() < min_obs:
            # Creates a mask to use as filter.
            clim_mask = country_climate_data["NAME"]!=station
            # Take rows which this applies.
            country_climate_data = country_climate_data.loc[clim_mask]
    
    ## Applying Linear Regression to Remaining Data ##
    # Climate regression on all datapoints.
    temp_regression = country_climate_data.groupby(["NAME","LATITUDE","LONGITUDE"]).apply(climate_regression)
    # Readjusting into a DataFrame. 
    temp_regression = temp_regression.reset_index().round(4)
    
    ## Plotting the Function ##
    color_map = px.colors.diverging.Portland
    fig = px.scatter_mapbox(temp_regression,
                           lat = "LATITUDE",
                           lon = "LONGITUDE",
                           hover_name = "NAME",
                           color_continuous_scale=color_map,
                           labels = {
                              "0":"Estimated Yearly Increase (C)",
                               "LATITUDE":"Latitude",
                               "LONGITUDE":"Longitude"
                          },
                           color = 0,
                           **kwargs)
    
    fig.update_layout(mapbox_style="carto-positron")
    fig.update_layout(margin={"r":0,"t":40,"l":100,"b":0})
    return fig
    
    
## Climate Latitude Query Function ##
def climate_latitude_query(lat_range, year_begin, year_end):
    """
    The climate_latitude_query() function uses SQL to
    collect temperature data based on latitude ranges
    and year data. The function returns a DataFrame
    containing the appropriate data. 
    Output: DataFrame.
    --
    Parameters:
    - lat_range: int. Latitude range away from 0 to
    consider. Data pulled from range -(lat_range) to
    lat_range.
    - year_begin: int. Starting year to examine.
    - year_end: int. Ending year to examine.
    """
    ## Writing SQL function. ##
    conn = sqlite3.connect("noaa.db")

    ## Finding region by latitude and years. ##
    cmd = \
    f"""
    SELECT S.name, S.latitude, S.longitude, T.id, T.year, T.month, T.temp
    FROM temperatures T
    LEFT JOIN stations S on T.id = S.id
    WHERE S.latitude > -{lat_range}
    AND S.latitude < {lat_range}
    AND T.year<{year_end}
    AND T.year>{year_begin}
    """
    
    ## Writing to DataFrame ##
    query_df = pd.read_sql_query(cmd, conn)
    
    ## Close SQL Function ##
    conn.close()
    
    return query_df


## Latitude Scatter Function ##
def latitude_scatter(lat_range, year_begin, year_end, **kwargs):
    """
    The latitude_scatter() function uses the
    climate_latitude_query() function to generate data and
    produce a scatterplot of the estimated yearly change
    of temperature. 
    Output: Plotly Scatterplot Figure
    --
    Parameters: 
    - lat_range: int. Latitude range away from 0 to
    consider. Data pulled from range -(lat_range) to
    lat_range.
    - year_begin: int. Starting year to examine.
    - year_end: int. Ending year to examine.
    - **kwargs allows for passing into px.scatter().
    """
    ## Create DataFrame ##
    # Calling on previous function.
    climate_lat_data = climate_latitude_query(lat_range,year_begin,year_end)
    
    # Climate regression on all datapoints.
    climate_lat_data = climate_lat_data.groupby(["NAME","LATITUDE","LONGITUDE"]).apply(climate_regression)
    # # Readjusting into a DataFrame. 
    climate_lat_data = climate_lat_data.reset_index().round(4)

    # Creating true/false section for computations
    mask = pd.DataFrame(climate_lat_data["LATITUDE"]>0)
    mask = mask.rename(columns={"LATITUDE":"Above"})

    # Adding true/false to DataFrame
    climate_lat_data = climate_lat_data.join(mask)

    lat_scatter = px.scatter(climate_lat_data,x="LATITUDE",y=0,
                     labels={
                         "0":"Estimated Yearly Change (C)",
                         "LATITUDE":"Latitude"
                     },
                     title = "Estimated Yearly Temperature Increase by Latitude (C)",
                     color="LONGITUDE",
                     facet_col="Above",
                     **kwargs
                    )
    return lat_scatter


## Latitude Mean Histogram Function ##
def latitude_mean_hist(lat_range, year_begin, year_end, **kwargs):
    """
    The latitude_mean_hist() function...
    Output: Plotly Histogram Figure
    -- 
    Parameters:
    - lat_range: int. Latitude range away from 0 to
    consider. Data pulled from range -(lat_range) to
    lat_range.
    - year_begin: int. Starting year to examine.
    - year_end: int. Ending year to examine.
    - **kwargs allows for passing into px.scatter().
    """
    ## Create DataFrame ##
    # Calling on previous function.
    climate_lat_data = climate_latitude_query(lat_range,year_begin,year_end)
    
    # Climate regression on all datapoints.
    climate_lat_data = climate_lat_data.groupby(["NAME","LATITUDE","LONGITUDE"]).apply(climate_regression)
    # # Readjusting into a DataFrame. 
    climate_lat_data = climate_lat_data.reset_index().round(4)

    # Creating true/false section for computations
    mask = pd.DataFrame(climate_lat_data["LATITUDE"]>0)
    mask = mask.rename(columns={"LATITUDE":"Above"})
    
    # Adding true/false to DataFrame
    climate_lat_data = climate_lat_data.join(mask)
    
    ## Including Mean Values ## 
    mean_set = climate_lat_data["Above"]==1
    mean_df = pd.DataFrame([["Below 0",climate_lat_data[mean_set][0].mean()],
                        ["Above 0",(climate_lat_data[~mean_set])[0].mean()]])

    ## Plotting the Histogram ##
    lat_mean = px.histogram(mean_df,x=0,y=1,
                labels={
                    "0":"Below or Above Latitude 0",
                    "1":"Mean of Estimated Yearly Increase"
                },
                title = "Means of Yearly Change by Latitude")
    
    return lat_mean