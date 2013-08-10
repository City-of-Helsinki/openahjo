class IssueListItemView extends Backbone.View
    tagName: 'li'
    className: 'issue'
    template: _.template $("#issue-list-item-template").html()

    render: ->
        model = @model.toJSON()
        text = model.search_highlighted
        if text
            cut_amount = 200
            i = text.indexOf '<em'
            if i > cut_amount
                j = i - cut_amount
                # split on word boundaries
                while j > 0 and /[^\s]/.test text[j]
                    j--
                text = '... ' + text[j+1..]
            i = text.indexOf '/em>'
            if text.length - i > cut_amount
                j = i + cut_amount
                while j < text.length and /[^\s]/.test text[j]
                    j++
                text = text[0..j-1] + '...'
            model.search_highlighted = text

        labels = []
        labels.push
            text: @model.get 'top_category_name'
            'class': 'info'

        districts = {}
        for d in @model.get 'districts'
            districts[d.name] = d
        for d of districts
            labels.push
                text: d
                'class': 'inverse'

        model.label_list = labels
        model.view_url = @model.get_view_url()
        html = $($.trim(@template model))
        @$el.html html
        return @

class IssueListCountView extends Backbone.View
    el: "#result-count"

    initialize: ->
        @listenTo @collection, 'reset', @render

    render: ->
        res_count = @collection.meta.total_count
        $("#result-count .count").html res_count
        $("#result-count").show()

class IssueListView extends Backbone.View
    tagName: 'ul'
    className: 'issue-list-items'

    initialize: ->
        @listenTo @collection, 'reset', @render
        @listenTo @collection, 'add', @render_one
        $(window).on 'scroll', @handle_scroll
        @issue_views = []

    remove: ->
        super()
        $(window).off 'scroll', @handle_scroll

    handle_scroll: (ev) =>
        if @fetching or not @rendered
            return

        if @collection.length >= @collection.meta.total_count
            return

        trigger_point = 100
        pixels_left = $(document).height() - ($(window).height() + $(window).scrollTop())
        if pixels_left > trigger_point
            return

        @fetching = true
        @page++
        @collection.fetch
            data:
                page: @page
            add: true
            remove: false
            success: => @fetching = false
            error: => @fetching = false

    render_one: (issue) ->
        view = new IssueListItemView model: issue
        @issue_views.push view
        @$el.append view.render().$el

    render: ->
        for view in @issue_views
            view.remove()
        @issue_views = []
        @page = 1
        @collection.each (issue) =>
            @render_one issue
        @list_rendered = true
        return @

    disable: ->
        @disabled = true

class IssueMapView extends Backbone.View
    tagName: 'div'
    className: 'map'

    initialize: (opts) ->
        @geometries = []
        @listenTo @collection, 'reset', @render
        @listenTo @collection, 'add', @render_one

        opts.parent_el.append @el

        @map = L.map(@el).setView [60.170833, 24.9375], 12
        L.tileLayer('http://{s}.tile.cloudmade.com/{key}/{style}/256/{z}/{x}/{y}.png',
            attribution: 'Map data &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery © <a href="http://cloudmade.com">CloudMade</a>',
            maxZoom: 18
            key: 'BC9A493B41014CAABB98F0471D759707'
            style: 998
        ).addTo @map

        @map.on 'moveend', @map_move

    render_one: (issue) =>
        for geom_json in issue.get 'geometries'
            if geom_json.type != 'Point'
                continue
            geom = L.geoJson geom_json
            geom.bindPopup "<b>#{geom_json.name}</b><br><a href='#{issue.get_view_url()}'>#{issue.get 'subject'}</a>"
            geom.addTo @map
            geom_json.geometry = geom
            @geometries.push geom

    remove_one: (issue) =>
        for geom_json in issue.get 'geometries'
            if not geom_json.geometry
                continue
            @map.removeLayer geom_json.geometry
            delete geom_json.geometry

    get_map_bounds: ->
        return @map.getBounds().toBBoxString()
    map_move: (ev) =>
        @trigger "map-move", @get_map_bounds()

    render: ->
        for geom in @geometries
            @map.removeLayer geom
        @geometries = []
        @collection.each @render_one

class CategorySelectView extends Backbone.View
    el: '#category-filter'
    events:
        'click .category-list li a': 'select_category'

    initialize: (opts) ->
        @listenTo @collection, 'reset', @render
        @parent_view = opts.parent_view

    make_li: (cat, $parent) ->
        $li = $("<li><a tabindex='-1' data-cat-id='#{cat.get 'id'}' href='#'>#{cat.get 'origin_id'} #{cat.get 'name'}</a></li>")
        if cat.children and cat.children.length
            $li.addClass "dropdown-submenu"
            $list_el = $("<ul class='dropdown-menu'></ul>")
            $li.append $list_el
            for kitten in cat.children
                @make_li kitten, $list_el
        $parent.append $li

    select_category: (ev) =>
        ev.preventDefault()
        el = ev.currentTarget
        cat_id = $(el).data 'cat-id'
        cat = @collection.findWhere id: cat_id
        $("#category-filter input").val "#{cat.get 'origin_id'} #{cat.get 'name'}"
        @parent_view.set_filter 'category', cat.get 'id'

    render: ->
        $list = @$el.find '.category-list'
        $list.empty()
        root_list = @collection.filter (cat) -> cat.get('level') == 0
        _.each root_list, (cat) =>
            @make_li cat, $list

class PolicymakerSelectView extends Backbone.View
    el: "#policymaker-filter"
    initialize: (opts) ->
        @parent_view = opts.parent_view

    render: ->
        @$el.empty()
        @collection.each (pm) =>
            opt_el = $("<option value='#{pm.get 'id'}'>#{pm.get 'name'}</option>")
            @$el.append opt_el
        @$el.chosen(CHOSEN_DEFAULTS).change @select_category

    select_category: (ev) =>
        val = @$el.val()
        if val
            pm_list = (parseInt x for x in @$el.val()).join ','
        else
            pm_list = null
        @parent_view.set_filter 'policymaker', pm_list

class IssueSearchView extends Backbone.View
    el: "#content-container"

    initialize: (opts) ->
        @cat_list = new CategoryList opts.cat_models
        @cat_select_view = new CategorySelectView
            collection: @cat_list
            parent_view: @
        @cat_select_view.render()

        @pm_list = new PolicymakerList opts.pm_models
        @pm_select_view = new PolicymakerSelectView
            collection: @pm_list
            parent_view: @
        @pm_select_view.render()

        if not @issue_list
            @issue_list = new IssueSearchList

        @count_view = new IssueListCountView collection: @issue_list

        @$el.find("#text-filter").change @handle_text_filter

        $(".list-tab-selector .select-list").click @select_list
        $(".list-tab-selector .select-map").click @select_map

    handle_text_filter: (ev) =>
        el = $(ev.target)
        q = $.trim el.val()
        if q
            @set_filter 'text', q
        else
            @set_filter 'text', null

    select_list: ->
        router.navigate "/", trigger: true
    select_map: ->
        router.navigate "map/", trigger: true

    select: (view_type) ->
        if view_type == @view_type
            return
        if @result_view
            @result_view.remove()

        filters = {}

        parent_el = @$el.find('#issue-list-items-container')
        if view_type == 'list'
            @result_view = new IssueListView collection: @issue_list
            @$el.find(".list-tab-selector .select-list").addClass "active"
            @$el.find(".list-tab-selector .select-map").removeClass "active"
            @view_type = 'list'
            parent_el.append @result_view.el
            filters.bbox = null
        else
            @result_view = new IssueMapView collection: @issue_list, parent_el: parent_el
            @$el.find(".list-tab-selector .select-map").addClass "active"
            @$el.find(".list-tab-selector .select-list").removeClass "active"
            @view_type = 'map'
            @listenTo @result_view, 'map-move', @map_move
            filters.bbox = @result_view.get_map_bounds()

        text_filter = $("#text-filter").val()
        if text_filter
            filters.text = text_filter
        else
            filters.text = null

        @set_filters filters

    map_move: (args) ->
        @set_filter 'bbox', args

    set_filter: (type, query) ->
        @issue_list.set_filter type, query
        @issue_list.fetch reset: true

    set_filters: (filters) ->
        for type of filters
            @issue_list.set_filter type, filters[type]
        @issue_list.fetch reset: true

class IssueRouter extends Backbone.Router
    routes:
        "": "issue_list"
        "map/": "issue_map"

    issue_list: ->
        search_view.select 'list'

    issue_map: ->
        search_view.select 'map'


search_view = new IssueSearchView
    cat_models: cat_list_json
    pm_models: pm_list_json

router = new IssueRouter
Backbone.history.start {pushState: true, root: "/issue/"}

###
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
###
