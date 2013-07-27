DATE_FORMAT = 'D.M.YYYY'
VIEW_BASE_URL = API_PREFIX + 'policymaker/'

class AgendaItem extends Backbone.Tastypie.Model

class AgendaItemList extends Backbone.Tastypie.Collection
    urlRoot: API_PREFIX + 'v1/agenda_item/'
    model: AgendaItem

class Meeting extends Backbone.Tastypie.Model
    get_view_url: ->
        pm = @collection.policymaker_list.get @get('policymaker')
        return pm.get_view_url() + "#{@get 'year'}/#{@get 'number'}/"

    initialize: ->
        @agenda_item_list = new AgendaItemList
        @agenda_item_list.filters['meeting'] = @get 'id'
        @agenda_item_list.filters['limit'] = 1000

    fetch_agenda_items: ->
        if @agenda_item_list.length
            @agenda_item_list.trigger 'reset'
            return
        @agenda_item_list.fetch reset: true

class MeetingList extends Backbone.Tastypie.Collection
    urlRoot: API_PREFIX + 'v1/meeting/'
    model: Meeting

    initialize: (models, opts)->
        @policymaker_list = opts.policymaker_list

class Policymaker extends Backbone.Tastypie.Model
    initialize: ->
        @meeting_list = new MeetingList null, policymaker_list: @collection
        @meeting_list.filters['policymaker'] = @get 'id'
        @meeting_list.filters['limit'] = 1000

    get_view_url: ->
        return VIEW_BASE_URL + @get('slug') + '/'
    get_category: ->
        abbrev = @get('abbreviation')
        if not abbrev
            return null
        if abbrev == 'Khs'
            return 'government'
        else if abbrev == 'Kvsto'
            return 'council'
        name = @get('name')
        if name.indexOf('lautakunta') >= 0
            return 'committee'
        if name.indexOf('johtokunta') >= 0 or name.indexOf(' jk') >= 0
            return 'board'
        return 'other'

    fetch_meetings: ->
        if @meeting_list.length
            @meeting_list.trigger 'reset'
            return
        @meeting_list.fetch reset: true

class PolicymakerList extends Backbone.Tastypie.Collection
    urlRoot: API_PREFIX + 'v1/policymaker/'
    model: Policymaker

PM_VIEW_INFO =
    'Kslk':
        hyphen_names: ['Kaupunki-', 'suunnittelu-', 'lautakunta']
    'Sotelk':
        hyphen_names: ['Sosiaali-', 'ja terveys-', 'lautakunta']
    'Tplk':
        hyphen_names: ['Teknisen', 'palvelun', 'lautakunta']
    'Vakalk':
        hyphen_names: ['Varhais-', 'kasvatus-', 'lautakunta']
    'Kklk':
        hyphen_names: ['Kulttuuri- ja', 'kirjasto-', 'lautakunta']

class PolicymakerListNavView extends Backbone.View
    el: '.policymaker-nav'

    initialize: ->
        @collection.on 'reset', @render, @
        @active_category = null
    render: ->
        COMPONENTS = [
            {name: 'Kaupunginvaltuusto', category: 'council'}
            {name: 'Kaupunginhallitus', category: 'government'}
            {name: 'Lautakunnat', category: 'committee'}
            {name: 'Johtokunnat', category: 'board'}
            {name: 'Muut', category: 'other'}
        ]
        @$el.empty()
        $li = $("<li class='list'><a href='#{VIEW_BASE_URL}'>Päättäjät</a></li>")
        if @active_section == 'list'
            $li.addClass 'active'
        @$el.append $li
        for c in COMPONENTS
            list = @collection.filter (m) -> m.get_category() == c.category
            list = _.sortBy list, (m) -> m.get 'name'
            if list.length > 1
                $li = $("<li class='dropdown'><a class='dropdown-toggle' data-toggle='dropdown' href='#'>#{c.name} <b class='caret'></b>")
                $ul = $("<ul class='dropdown-menu'></ul>")
                $li.append $ul
                list.forEach (m) ->
                    $el = $("<li><a href='#{m.get_view_url()}'>#{m.get 'name'}</a></li>")
                    $ul.append $el
            else
                m = list[0]
                $li = $("<li><a href='#{m.get_view_url()}'>#{c.name}</a></li>")

            $li.addClass c.category
            if @active_section == c.category
                $li.addClass 'active'
            @$el.append $li

        @$el.find('li > a').click (ev) ->
            if router.navigate_to_link @
                ev.preventDefault()

    set_category: (category) ->
        @$el.find('li').removeClass 'active'
        @$el.find('li.' + category).addClass 'active'
        @active_category = category

class PolicymakerListItemView extends Backbone.View
    tagName: 'a'
    className: 'org-box'
    template: $("#policymaker-list-item-template").html()

    format_title: ->
        name = @model.get 'name'
        abbrev = @model.get 'abbreviation'
        if abbrev of PM_VIEW_INFO
            vi = PM_VIEW_INFO[abbrev]
            if 'hyphen_names' of vi
                return vi.hyphen_names.join('<br/>')
        lk_idx = name.indexOf 'lautakunta'
        if lk_idx >= 0
            prev_char = name[lk_idx-1]
            if prev_char != ' ' and prev_char != '-'
                hyphen = '-'
            else
                hyphen = ''

            name = name[0..lk_idx-1] + hyphen + '<br/>' + name[lk_idx..]
        return name
    render: ->
        model = @model.toJSON()
        model.title = @format_title()
        model.icon = 'search'
        html = _.template @template, model
        @$el.addClass @model.get_category()
        @$el.attr 'href', @model.get_view_url()
        @$el.append html
        return @

class PolicymakerListView extends Backbone.View
    tagName: 'div'
    className: 'policymaker-list'

    render_pm_section: (list, heading, big) ->
        list = _.sortBy list, (m) -> m.get 'name'
        $container = @$el
        if heading
            $container.append $("<h2>#{heading}</h2>")
        row_idx = 0
        $row = $("<div class='row'></div>")
        list.forEach (m) ->
            view = new PolicymakerListItemView {model: m}
            view.render()
            $el = view.$el
            $row.append view.$el
            row_idx++
            if big
                $el.addClass 'span9'
                $container.append $row
                $row = $("<div class='row'></div>")
                row_idx = 0
            else
                $el.addClass 'span3'
                if row_idx == 3
                    $container.append $row
                    row_idx = 0
                    $row = $("<div class='row'></div>")
        if row_idx
            $container.append $row

    render: ->
        council = @collection.filter (m) -> m.get_category() == 'council'
        @render_pm_section council, null, true

        gov = @collection.filter (m) -> m.get_category() == 'government'
        @render_pm_section gov, null, true

        committees = @collection.filter (m) -> m.get_category() == 'committee'
        @render_pm_section committees, "Lautakunnat", false

        boards = @collection.filter (m) -> m.get_category() == 'board'
        @render_pm_section boards, "Johtokunnat", true

        others = @collection.filter (m) -> m.get_category() == 'other'
        @render_pm_section others, "Muut", true

class PolicymakerDetailsView extends Backbone.View
    tagName: 'div'
    className: 'policymaker-details'
    template: _.template $("#policymaker-details-template").html()

    initialize: ->
        @listenTo @model.meeting_list, 'reset', @render_meeting_list
        @listenTo @model.meeting_list, 'reset', @_select_meeting

    format_date: (date) ->
        m = moment date
        return m.format DATE_FORMAT

    render: ->
        model = @model.toJSON()
        html = @template model
        @$el.html html
        return @

    render_meeting_list: ->
        list = @model.meeting_list
        $list_el = @$el.find('.meeting-list').first()
        $list_el.empty()
        template = _.template $("#policymaker-meeting-list-item-template").html()
        list.each (meeting) =>
            model = meeting.toJSON()
            model.date_str = @format_date meeting.get('date')
            model.view_url = meeting.get_view_url()
            $li = $($.trim(template model))
            $li.click (ev) ->
                link_el = $(@).find('> a')
                if router.navigate_to_link link_el
                    ev.preventDefault()
            $list_el.append $li

    render_meeting_details: ->
        meeting = @selected_meeting
        template = _.template $("#policymaker-meeting-details-template").html()
        model = meeting.toJSON()
        model.date_str = @format_date meeting.get('date')

        agenda_items = []
        meeting.agenda_item_list.each (ai) ->
            m = ai.toJSON()
            agenda_items.push m
        model.agenda_items = agenda_items

        meeting_list = @model.meeting_list
        idx = meeting_list.indexOf meeting
        if idx > 0
            model.next_meeting = meeting_list.at(idx - 1).get_view_url()
        else
            model.next_meeting = null
        if idx < meeting_list.length - 1
            model.prev_meeting = meeting_list.at(idx + 1).get_view_url()
        else
            model.prev_meeting = null

        html = $.trim template(model)
        @$el.find('.meeting-details').first().html html

        @$el.find('.back-fwd a').click (ev) ->
            if router.navigate_to_link @
                ev.preventDefault()

    _select_meeting: ->
        meeting_list = @model.meeting_list
        if @selected_meeting
            @stopListening @selected_meeting.agenda_item_list

        if @selected_meeting_id
            if @selected_meeting_id == 'next'
                idx = meeting_list.indexOf @selected_meeting
                if idx > 0
                    idx--
                meeting = meeting_list.at idx
            else if @selected_meeting_id == 'prev'
                idx = meeting_list.indexOf @selected_meeting
                if idx < meeting_list.length - 1
                    idx++
                meeting = meeting_list.at idx
            else
                meeting = meeting_list.find (m) =>
                    year = m.get('year')
                    number = m.get('number')
                    id = "#{year}/#{number}"
                    return id == @selected_meeting_id
        else
            # If meeting id is not specified, choose the first (latest) meeting.
            meeting = meeting_list.at 0

        @listenTo meeting.agenda_item_list, 'reset', @render_meeting_details
        @selected_meeting = meeting
        meeting.fetch_agenda_items()

    select_meeting: (@selected_meeting_id) ->
        @model.fetch_meetings()

policymaker_list = new PolicymakerList policymakers
nav_view = new PolicymakerListNavView {collection: policymaker_list}
nav_view.render()

list_view = new PolicymakerListView {collection: policymaker_list}

class PolicymakerRouter extends Backbone.Router
    routes:
        "": "pm_list"
        ":slug/": "pm_details"
        ":slug/:year/:number/": "pm_details"

    navigate_to_link: (el) ->
        href = $(el).attr 'href'
        if href.indexOf(VIEW_BASE_URL) != 0
            return false
        href = href[VIEW_BASE_URL.length..]
        Backbone.history.navigate href, true
        return true

    pm_list: ->
        $("#content-container > h1").html "Päättäjät"
        document.title = "Päättäjät"
        nav_view.set_category 'list'
        list_view.render()
        $(".policymaker-content").empty()
        $(".policymaker-content").append list_view.$el

    pm_details: (slug, year, number) ->
        pm = policymaker_list.filter (m) -> m.get('slug') == slug
        pm = pm[0]
        nav_view.set_category pm.get_category()
        $("#content-container > h1").html pm.get('name')
        document.title = pm.get 'name'
        details_view = new PolicymakerDetailsView model: pm
        # Choose the latest meeting by default
        details_view.render()
        if year and number
            meeting_id = "#{year}/#{number}"
        else
            meeting_id = null
        details_view.select_meeting meeting_id
        $(".policymaker-content").empty()
        $(".policymaker-content").append details_view.$el

router = new PolicymakerRouter

Backbone.history.start {pushState: true, root: "/policymaker/"}
