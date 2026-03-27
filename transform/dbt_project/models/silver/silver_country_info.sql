{{ config(materialized='table', schema='silver') }}

with source as (
    select
        city_slug,
        display_name,
        country_name,
        country_code,
        region,
        subregion,
        capital,
        population,
        currencies,
        languages,
        timezones
    from travel_intel.bronze.restcountries
),

-- Map correct city-level timezone from known city slugs
-- We cannot trust the timezones column for multi-timezone countries
-- (US has 11, UK has 9) — so we hardcode city timezone from cities.yml knowledge
city_timezone as (
    select
        city_slug,
        case city_slug
            when 'new_york'  then 'UTC-05:00'
            when 'london'    then 'UTC+00:00'
            when 'tokyo'     then 'UTC+09:00'
            when 'barcelona' then 'UTC+01:00'
            when 'bangkok'   then 'UTC+07:00'
        end as primary_timezone
    from source
)

select
    s.city_slug,
    s.display_name,
    s.country_name,
    s.country_code,
    s.region,
    s.subregion,
    s.capital,
    s.population,
    s.currencies,
    s.languages,
    t.primary_timezone
from source s
join city_timezone t on s.city_slug = t.city_slug