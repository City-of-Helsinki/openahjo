
recent_items = []
latest_meetings = []

format_date = (date_in) ->
    return moment(date_in, 'YYYY-MM-DD').format('L')

format_view_url = (view, item_id) ->
    return VIEW_URLS[view].replace 'ID', item_id

render_list_elements = ($list_el, items, template) ->
    list_height = $list_el.height()
    item_count = 0
    for item in items
        $item_el = $(_.template template, item)
        $item_el.css {'visibility': 'hidden'}
        $list_el.append $item_el
        if $item_el[0].offsetTop + $item_el[0].offsetHeight > list_height
            $item_el.remove()
            break
        item_count++
        $item_el.css {'visibility': 'visible'}
    return item_count

render_recent_items = ->
    $list_el = $(".recent-items ul")
    for item in recent_items
        item.view_url = format_view_url 'issue-details', item.issue.slug
    template = "<li><a href='<%= view_url %>'><%= subject %></a></li>"

    item_index = 0
    fade_delay = 0
    carousel = ->
        $list_el.css({'visibility': 'hidden'}).empty().show()
        count = render_list_elements $list_el, recent_items[item_index..], template
        item_index += count
        if item_index >= recent_items.length
            item_index = 0
        $list_el.hide().css({'visibility': 'visible'}).fadeIn fade_delay
        setTimeout fade_out, 15000
    fade_out = ->
        $list_el.fadeOut fade_delay, carousel

    carousel()
    fade_delay = 100

render_latest_meetings = ->
    $list_el = $(".latest-meetings ul")
    for item in latest_meetings
        item.date_str = format_date item.date
        item.view_url = format_view_url 'meeting-details', item.id
    template = "<li><a href='<%= view_url %>'><%= policymaker_name %> <%= number %>/<%= year %> (<%= date_str %>)</a></li>"
    render_list_elements $list_el, latest_meetings, template

params = 
    order_by: '-meeting__date'
    limit: 20
    from_minutes: true
$.getJSON API_PREFIX + 'v1/agenda_item/', params, (data) ->
    recent_items = data.objects
    render_recent_items()

params =
    order_by: '-date'
    limit: 10
    minutes: true

$.getJSON API_PREFIX + 'v1/meeting/', params, (data) ->
    latest_meetings = data.objects
    render_latest_meetings()
