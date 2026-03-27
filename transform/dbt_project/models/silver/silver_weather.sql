{{ config(materialized='table', schema='silver') }}

with source as (
    select
        city_slug,
        display_name,
        cast(date as date)              as forecast_date,
        temp_max_c,
        temp_min_c,
        precipitation_mm,
        windspeed_max_kmh,
        description
    from travel_intel.bronze.weather
),

aggregated as (
    select
        city_slug,
        display_name,
        min(forecast_date)                                      as forecast_start,
        max(forecast_date)                                      as forecast_end,
        round(avg(temp_max_c), 1)                              as avg_temp_max_c,
        round(avg(temp_min_c), 1)                              as avg_temp_min_c,
        round(avg((temp_max_c + temp_min_c) / 2), 1)          as avg_temp_c,
        round(sum(precipitation_mm), 1)                        as total_precipitation_mm,
        count(case when precipitation_mm > 0 then 1 end)       as rainy_days,
        round(avg(windspeed_max_kmh), 1)                       as avg_windspeed_kmh
    from source
    group by city_slug, display_name
)

select * from aggregated