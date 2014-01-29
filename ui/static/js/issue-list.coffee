DATE_FORMAT = 'D.M.YYYY'

TRANSLATIONS = {
    "draft resolution": "Päätösesitys"
    "presenter": "Esittelijä"
    "resolution": "Päätös"
    "summary": "Yhteenveto"
}
LOCATIONS_FI =
    'address': 'Osoite'
    'plan': 'Kaava'
    'plan_unit': 'Kaavayksikkö'
RESOLUTIONS_EN =
    'PASSED': 'Passed as drafted'
    'PASSED_VOTED': 'Passed after a vote'
    'PASSED_REVISED': 'Passed revised by presenter'
    'PASSED_MODIFIED': 'Passed modified'
    'REJECTED': 'Rejected'
    'NOTED': 'Noted as informational'
    'RETURNED': 'Returned to preparation'
    'REMOVED': 'Removed from agenda'
    'TABLED': 'Tabled'
    'ELECTION': 'Election'
RESOLUTIONS_FI =
    'PASSED': 'Ehdotuksen mukaan'
    'PASSED_VOTED': 'Ehdotuksen mukaan äänestyksin'
    'PASSED_REVISED': 'Esittelijän muutetun ehdotuksen mukaan'
    'PASSED_MODIFIED': 'Esittelijän ehdotuksesta poiketen'
    'REJECTED': 'Hylättiin'
    'NOTED': 'Merkittiin tiedoksi'
    'RETURNED': 'Palautettiin'
    'REMOVED': 'Poistettiin'
    'TABLED': 'Jätettiin pöydälle'
    'ELECTION': 'Vaali'
RESOLUTIONS_ICONS =
    'PASSED': 'ok'
    'PASSED_VOTED': 'hand-up'
    'PASSED_REVISED': 'ok-circle'
    'PASSED_MODIFIED': 'ok-sign'
    'REJECTED': 'trash'
    'NOTED': 'exclamation-sign'
    'RETURNED': 'repeat'
    'REMOVED': 'remove'
    'TABLED': 'inbox'
    'ELECTION': 'group'

MAP_ATTRIBUTION =
    'Map data &copy;
     <a href="http://openstreetmap.org">OpenStreetMap</a>
     contributors,
     <a href="http://creativecommons.org/licenses/by-sa/2.0/">
     CC-BY-SA</a>,
     Imagery © <a href="http://cloudmade.com">CloudMade</a>'

create_map = (container_element, map_attribution) ->
    L.map container_element,
          layers: [
            L.tileLayer 'http://{s}.tile.cloudmade.com/{key}/' +
                '{style}/256/{z}/{x}/{y}.png',
                attribution: map_attribution
                maxZoom: 18
                key: 'BC9A493B41014CAABB98F0471D759707'
                style: 998]

class IssueView extends Backbone.View
    make_labels: ->
        labels = []
        labels.push
            text: @model.get 'top_category_name'
            'class': 'category'

        districts = {}
        for d in @model.get 'districts'
            districts[d.name] = d
        for d of districts
            labels.push
                text: d
                'class': 'district'
        return labels

class IssueListItemView extends IssueView
    tagName: 'li'
    className: 'issue'
    template: _.template $("#issue-list-item-template").html()

    render: ->
        model = @model.toJSON()
        model.latest_decision_date = moment(model.latest_decision_date).format DATE_FORMAT
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

        model.label_list = @make_labels()
        model.view_url = @model.get_view_url()
        html = $($.trim(@template model))
        @$el.html html
        return @

class IssueListCountView extends Backbone.View
    el: "#result-count"

    initialize: ->
        @listenTo @collection, 'reset', @render
        @listenTo @collection, 'request', @clear

    clear: =>
        # Only clear result count if it's not a paging request.
        if @collection.length != 0
            return
        $("#result-count").hide()

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
            spinner: $(".issue-list-spinner")

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
        @rendered = true
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

        @map = create_map(@el, MAP_ATTRIBUTION).setView [60.170833, 24.9375], 12
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
        if not cat_id
            $("#category-filter input").val ""
            @parent_view.set_filter 'category', null
            return
        cat = @collection.findWhere id: cat_id
        $("#category-filter input").val "#{cat.get 'origin_id'} #{cat.get 'name'}"
        @parent_view.set_filter 'category', cat.get 'id'

    render: ->
        $list = @$el.find '.category-list'
        $list.empty()
        $list.append $("<li><a tabindex='-1' href='#'>Ei tehtäväluokkarajausta</a></li>")
        $list.append $("<li class='divider'></li>")
        root_list = @collection.filter (cat) -> cat.get('level') == 0
        _.each root_list, (cat) =>
            @make_li cat, $list

class DistrictSelectView extends Backbone.View
    el: '#district-filter'
    initialize: (opts) ->
        @parent_view = opts.parent_view
    render: ->
        @$el.empty()
        district_dict = {}
        @collection.each (d) =>
            district_dict[d.get 'name'] = d
        district_names = []
        for name of district_dict
            district_names.push name
        district_names = _.sortBy district_names, (x) -> x

        @$el.append "<option value=''></option>"
        _.each district_names, (d) =>
            opt_el = $("<option value='#{d}'>#{d}</option>")
            @$el.append opt_el
        chosen_opts = _.extend {allow_single_deselect: true}, CHOSEN_DEFAULTS
        @$el.chosen(chosen_opts).change @select_district

    select_district: (ev) =>
        val = @$el.val()
        if val
            d_list = val.join ','
        else
            d_list = null
        @parent_view.set_filter 'district', d_list

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
    el: "#subpage-content-container"
    template: $("#issue-search-template").html()

    initialize: (opts) ->
        content = $.trim @template
        @$el.html content

        @pm_list = opts.pm_list
        @cat_list = opts.cat_list
        @district_list = opts.district_list

        @cat_select_view = new CategorySelectView
            collection: @cat_list
            parent_view: @
        @cat_select_view.render()

        @district_select_view = new DistrictSelectView
            collection: @district_list
            parent_view: @
        @district_select_view.render()

        @pm_select_view = new PolicymakerSelectView
            collection: @pm_list
            parent_view: @
        @pm_select_view.render()

        if opts.issue_list
            @issue_list = opts.issue_list
        else
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
        if window.history and window.history.replaceState
            url = $.param.querystring location.href, q: q, 2
            window.history.replaceState {}, window.title, url

    select_list: ->
        router.navigate "/", trigger: true
    select_map: ->
        router.navigate "kartta/", trigger: true

    select: (view_type) ->
        if view_type == @view_type
            return
        if @result_view
            @result_view.remove()

        params = $.deparam.querystring()
        filters = {}
        if 'q' of params
            $("#text-filter").val params['q']

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
        @issue_list.reset()
        @issue_list.fetch
            reset: true
            spinner: $(".issue-list-spinner")

    set_filters: (filters) ->
        for type of filters
            @issue_list.set_filter type, filters[type]
        @issue_list.reset()
        @issue_list.fetch
            reset: true
            spinner: $(".issue-list-spinner")


class IssueDetailsView extends IssueView
    el: "#subpage-content-container"
    template: _.template $("#item-details-template").html()
    meeting_template: _.template $("#meeting-template").html()

    initialize: (opts) ->
        @pm_list = opts.pm_list
        @listenTo @model.agenda_item_list, 'reset', @render

    select_agenda_item: (@meeting_id) ->
        @render()
        return

    render: ->
        if not @model.agenda_item_list.length
            @model.fetch_agenda_items()
            return

        if @meeting_id
            @current_ai = @model.agenda_item_list.find_by_slug @meeting_id, @pm_list
            if not @current_ai
                throw "Agenda item with slug #{@meeting_id} not found"
        else
            @current_ai = @model.agenda_item_list.at(0)

        future_list = []
        past_list = []
        now = moment()
        current_ai_data = null
        @model.agenda_item_list.each (ai) =>
            meeting_date = moment ai.get('meeting').date

            data = ai.toJSON()
            data.meeting.date_str = meeting_date.format DATE_FORMAT
            data.has_non_public_attachments = ai.has_non_public_attachments()
            if ai.id == @current_ai.id
                data.is_active = true
                current_ai_data = data
            else
                data.is_active = false
            if data.resolution
                data.resolution_str = RESOLUTIONS_FI[data.resolution]
                data.resolution_icon = RESOLUTIONS_ICONS[data.resolution]

            pm = @pm_list.get data.meeting.policymaker
            m = data.meeting
            m.icon = pm.get_icon()
            m.view_url = pm.get_view_url() + "#{m.year}/#{m.number}/"

            for c in data.content
                c.type_str = TRANSLATIONS[c.type]

            if meeting_date > now
                future_list.push data
            else
                past_list.push data

        data = @model.toJSON()
        data.future_list = future_list
        data.past_list = past_list
        data.current = current_ai_data
        data.label_list = @make_labels()

        data.meeting_template = @meeting_template
        html = $.trim(@template data)
        @$el.html html

        geometries = @model.get 'geometries'
        if geometries.length > 0
            @$el.find('#issue-map').css 'display', 'block'
            @map = create_map 'issue-map'
            @$el.find('#map-attribution').html '<hr>' + MAP_ATTRIBUTION

            geom_layer = L.geoJson null,
                onEachFeature: (featureData, layer) ->
                    layer.bindPopup "#{LOCATIONS_FI[featureData.category]}<br>
                                     <b>#{featureData.name}</b>"

            for geom_json in geometries
                geom_layer.addData geom_json
                geom_json.geometry = geom_layer

            geom_layer.addTo @map

            preferred_max_zoom = 16

            @map.fitBounds geom_layer.getBounds(),
                paddingBottomRight: [0, 50]
                maxZoom: preferred_max_zoom

            if (@map.getZoom() > preferred_max_zoom)
                # Workaround: the fitBounds options attribute maxZoom isn't respected,
                # so we have to zoom out manually if we require a maximum initial zoom level
                # while enabling the user to zoom in manually later.
                @map.setZoom preferred_max_zoom, animate: false

        @$el.find(".meeting-list li").click (ev) =>
            if ev.target.tagName == 'A'
                return true
            ai_id = $(ev.currentTarget).data 'agenda-item-id'
            ai = @model.agenda_item_list.findWhere id: ai_id
            router.navigate "#{@model.get 'slug'}/#{ai.get_slug @pm_list}/",
                trigger: true
                replace: true


class IssueRouter extends Backbone.Router
    routes:
        "": "issue_list_view"
        "kartta/": "issue_map_view"
        ":issue/": "issue_details_view"
        ":issue/:meeting/": "issue_details_view"

    initialize: ->
        @current_view = null
        @cat_list = new CategoryList cat_list_json
        @pm_list = new PolicymakerList pm_list_json
        @district_list = new DistrictList district_list_json

    ensure_view: (type, model) ->
        if type == 'search'
            if not @current_view instanceof IssueSearchView
                @current_view.remove()
            @current_view = new IssueSearchView
                cat_list: @cat_list
                pm_list: @pm_list
                district_list: @district_list
            @issue_list = @current_view.issue_list
        else
            if not @current_view instanceof IssueDetailsView
                @current_view.remove()
            @current_view = new IssueDetailsView
                model: model
                cat_list: @cat_list
                pm_list: @pm_list
                district_list: @district_list

    issue_list_view: ->
        @ensure_view 'search'
        @current_view.select 'list'

    issue_map_view: ->
        @ensure_view 'search'
        @current_view.select 'map'

    issue_details_view: (issue, meeting) ->
        model = @issue_list.findWhere slug: issue
        @ensure_view 'details', model
        @current_view.select_agenda_item meeting


router = new IssueRouter

if typeof issue_json != 'undefined'
    issue_list = new IssueList [issue_json]
    issue_list.at(0).agenda_item_list.reset ai_list_json, silent: true
    router.issue_list = issue_list

Backbone.history.start {pushState: true, hashChange: false, root: VIEW_URLS['issue-list']}
