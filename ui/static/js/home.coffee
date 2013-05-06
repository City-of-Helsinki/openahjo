###
TRANSLATIONS = {
    "draft resolution": "Päätösesitys"
    "presenter": "Esittelijä"
    "resolution": "Päätös"
    "summary": "Yhteenveto"
}

show_meeting = (meeting, $parent) ->
    $next = $parent.next()
    if $next.prop('tagName') == 'OL'
        if $next.is(':visible')
            $next.slideUp()
        else
            $next.slideDown()
        return

    $.getJSON '/v1/agenda_item/', {meeting: meeting.id}, (data) ->
        $list = $("<ol></ol>")
        for obj in data.objects
            console.log obj
            content_html = ''
            for c in obj.content
                if c.type of TRANSLATIONS
                    type = TRANSLATIONS[c.type]
                else
                    type = c.type
                content_html += "<strong>#{type}</strong>#{c.text}"
            $el = $("<li><h4>#{obj.item.subject}</h4><div class='content hide'>#{content_html}</div></li>")
            $list.append $el
            $el.find('h4').css('cursor', 'pointer').click (ev) ->
                content = $(ev.target).parent().find('.content')
                if content.is(':visible')
                    content.slideUp()
                else
                    content.slideDown()
        $list.hide()
        $parent.after $list
        $list.slideDown()

$.getJSON '/v1/meeting/', (data) ->
    $list = $('#meeting-list')
    for obj in data.objects
      do (obj) ->
        $el = $('<button class="btn btn-primary btn-block">' + obj.committee_name + ' ' + obj.number + '/' + obj.year + '</button>')
        $list.append $el
        $el.click (ev) ->
            show_meeting obj, $el
###

map = L.map('map').setView [60.170833, 24.9375], 12
L.tileLayer('http://{s}.tile.cloudmade.com/{key}/{style}/256/{z}/{x}/{y}.png',
    attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://cloudmade.com">CloudMade</a>',
    maxZoom: 18
    key: 'BC9A493B41014CAABB98F0471D759707'
    style: 998
).addTo(map);
window.my_map = map

active_borders = null
active_category = null

issues = []
issue_template = Handlebars.compile $("#issue-list-template").html()

markers = []
refresh_issues = ->
    params = {limit: 1000}

    if active_borders
        bounds = active_borders.getBounds()
    else if not active_category?
        # If no other filters set, use map bounds as default.
        bounds = map.getBounds()
    else
        bounds = null
    if bounds?
        params['bbox'] = bounds.toBBoxString()

    if active_category?
        params['category'] = active_category

    list_el = $("#issue-list")
    $.getJSON API_PREFIX + 'v1/issue/', params, (data) ->
        issues = []
        list_el.empty()
        for m in markers
            map.removeLayer m
        markers = []
        for issue in data.objects
            #if not issue.geometries.length
            #    continue
            issue.details_uri = "#{API_PREFIX}issue/#{issue.slug}/"
            for geom in issue.geometries
                coords = geom.coordinates
                ll = new L.LatLng coords[1], coords[0]
                if active_borders
                    if not leafletPip.pointInLayer(ll, active_borders).length
                        continue
                issue.in_bounds = true
                marker = L.marker ll
                marker.bindPopup "<b>#{geom.name}</b><br><a href='#{issue.details_uri}'>#{issue.subject}</a>"
                marker.addTo map
                markers.push marker
            if active_borders? and not issue.in_bounds
                continue
            issue_html = issue_template issue
            issues.push issue
            list_el.append $($.trim(issue_html))

input_district_map = null

$(".district-input input").typeahead
    limit: 5
    remote:
        url: GEOCODER_API_URL + 'v1/district/?limit=5&input=%QUERY'
        filter: (data) ->
            objs = data.objects
            datums = []
            for obj in objs
                d = {value: obj.name, id: obj.id, borders: obj.borders, name: obj.name}
                datums.push d
            input_district_map = objs
            return datums

$(".district-input input").on 'typeahead:selected', (ev, datum) ->
    if active_borders
        map.removeLayer active_borders
    borders = L.geoJson datum.borders,
        style:
            weight: 2
    borders.bindPopup datum.name
    borders.addTo map
    active_borders = borders
    map.fitBounds borders.getBounds()
    refresh_issues()
    close_btn = $(".district-input .close")
    close_btn.parent().show()

$(".district-input .close").on 'click', (ev) ->
    map.removeLayer active_borders
    active_borders = null
    refresh_issues()
    $(this).parent().hide()
    $(".district-input input").val ''
    ev.preventDefault()

map.on 'moveend', (ev) ->
    refresh_issues()

input_category_list = null
###
$(".category-input input").typeahead
    source: (query, process_cb) ->
        $.getJSON(API_PREFIX + 'v1/category/', {input: query, issues: 1}, (data) ->
            objs = data.objects
            ret = []
            for obj in objs
                ret.push "#{obj.name} (#{obj.num_issues})"
            input_category_list = objs
            process_cb ret
        )
###

category_suggestion_template = Handlebars.compile """
{{value}} <strong>({{num_issues}})</strong>
"""
$(".category-input input").typeahead
    template: category_suggestion_template
    limit: 10
    remote:
        url: API_PREFIX + 'v1/category/?issues=1&limit=10&input=%QUERY'
        filter: (data) ->
            objs = data.objects
            datums = []
            for obj in objs
                d = {value: obj.name, num_issues: obj.num_issues, id: obj.id}
                datums.push d
            return datums

$(".category-input input").on 'typeahead:selected', (ev, datum) ->
    active_category = datum.id
    refresh_issues()
$(".category-input input").on 'typeahead:autocompleted', (ev, datum) ->
    active_category = datum.id
    refresh_issues()

refresh_issues()
