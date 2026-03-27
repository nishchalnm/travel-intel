{{ config(materialized='table', schema='silver') }}

with source as (
    select
        city_slug,
        display_name,
        title,
        source_name,
        cast(published_at as timestamp) as published_at,
        sentiment_hint
    from travel_intel.bronze.news
),

-- dedup by keeping one row per city+title using GROUP BY instead of window function
deduped as (
    select
        city_slug,
        max(display_name)       as display_name,
        title,
        min(published_at)       as published_at,
        max(sentiment_hint)     as sentiment_hint
    from source
    group by city_slug, title
),

aggregated as (
    select
        city_slug,
        max(display_name)                                               as display_name,
        count(*)                                                        as article_count,
        count(case when sentiment_hint = 'positive' then 1 end)        as positive_count,
        count(case when sentiment_hint = 'negative' then 1 end)        as negative_count,
        count(case when sentiment_hint = 'neutral'  then 1 end)        as neutral_count,
        string_agg(title, ' | ')                                        as headlines_concat,
        max(published_at)                                               as latest_article_at
    from deduped
    group by city_slug
)

select * from aggregated