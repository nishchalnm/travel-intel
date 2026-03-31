{{ config(materialized='table', schema='gold') }}

with weather as (
    select * from travel_intel.silver.silver_weather
),

pois as (
    select
        city_slug,
        string_agg(poi_name, ' | ' order by rank) as top_pois,
        string_agg(primary_kind, ' | ' order by rank) as top_poi_kinds
    from travel_intel.silver.silver_pois
    group by city_slug
),

news as (
    select * from travel_intel.silver.silver_news
),

country as (
    select * from travel_intel.silver.silver_country_info
)

select
    -- identity
    w.city_slug,
    w.display_name,

    -- weather
    w.avg_temp_max_c,
    w.avg_temp_min_c,
    w.avg_temp_c,
    w.total_precipitation_mm,
    w.rainy_days,
    w.avg_windspeed_kmh,
    w.forecast_start,
    w.forecast_end,

    -- pois
    p.top_pois,
    p.top_poi_kinds,

    -- news
    n.article_count,
    n.positive_count,
    n.negative_count,
    n.neutral_count,
    n.headlines_concat,
    n.latest_article_at,

    -- country
    c.country_name,
    c.region,
    c.currencies,
    c.languages,
    c.primary_timezone,
    c.population

from weather w
join pois    p on w.city_slug = p.city_slug
join news    n on w.city_slug = n.city_slug
join country c on w.city_slug = c.city_slug