{{ config(materialized='table', schema='silver') }}

with source as (
    select
        city_slug,
        display_name,
        poi_name,
        category,
        -- extract first element of comma-separated kinds string
        trim(split_part(kinds, ',', 1))     as primary_kind,
        rating,
        lat,
        lon
    from travel_intel.bronze.pois
),

ranked as (
    select
        *,
        row_number() over (
            partition by city_slug
            order by rating desc, poi_name asc   -- poi_name asc breaks ties deterministically
        ) as rank
    from source
)

select
    city_slug,
    display_name,
    rank,
    poi_name,
    category,
    primary_kind,
    rating,
    lat,
    lon
from ranked
where rank <= 5