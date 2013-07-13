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

geometries = []
refresh_issues = ->
    params = {limit: 100}

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
        for m in geometries
            map.removeLayer m
        geometries = []
        for issue in data.objects
            #if not issue.geometries.length
            #    continue
            issue.details_uri = "#{API_PREFIX}issue/#{issue.slug}/"
            for geom_json in issue.geometries
                geom = L.geoJson geom_json
                if geom_json.type == 'Point'
                    ll = geom.getBounds().getCenter()
                    #ll = new L.LatLng coords[1], coords[0]
                    if active_borders
                        if not leafletPip.pointInLayer(ll, active_borders).length
                            continue
                issue.in_bounds = true
                geom.bindPopup "<b>#{geom_json.name}</b><br><a href='#{issue.details_uri}'>#{issue.subject}</a>"
                geom.addTo map
                geometries.push geom
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
            color: "red"
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

"""
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
"""

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
###

params =
    level__lte: 1
    limit: 1000

$.getJSON API_PREFIX + 'v1/category/', params, (data) ->
    cats = _.sortBy data.objects, (x) -> "#{x.level} #{x.origin_id}"
    top_cats = []
    for cat in data.objects
        if cat.level == 0
            cat.children = []
            top_cats.push cat
            continue
        parent_id = parseInt(cat.parent.split("/").slice(-2)[0])
        for top_cat in top_cats
            if top_cat.id == parent_id
                top_cat.children.push cat
                break

    $filter_list_el = $("#category-filter ul")

    make_li = (cat, $parent) ->
        $el = $("<li><a tabindex='-1' href='#'>#{cat.origin_id} #{cat.name}</a></li>")
        if cat.children
            $el.addClass "dropdown-submenu"
            $list_el = $("<ul class='dropdown-menu'></ul>")
            $el.append $list_el
            for kitten in cat.children
                make_li kitten, $list_el
        $parent.append $el

    for cat in top_cats
        $el = make_li cat, $filter_list_el
