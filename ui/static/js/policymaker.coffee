DATE_FORMAT = 'D.M.YYYY'
VIEW_BASE_URL = API_PREFIX + 'policymaker/'

PM_VIEW_INFO =
    'Kslk':
        hyphen_names: ['Kaupunki&shy;suunnittelu&shy;lautakunta']
    'Sotelk':
        hyphen_names: ['Sosiaali- ja terveys&shy;lautakunta']
    'Tplk':
        hyphen_names: ['Teknisen palvelun lautakunta']
    'Vakalk':
        hyphen_names: ['Varhais&shy;kasvatus&shy;lautakunta']
    'Kklk':
        hyphen_names: ['Kulttuuri- ja kirjasto&shy;lautakunta']

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
                $li = $("<li class='dropdown'><a class='dropdown-toggle' data-toggle='dropdown' href='#'>#{c.name} <b class='caret'></b></a></li>")
                $ul = $("<ul class='dropdown-menu'></ul>")
                $li.append $ul
                for m in list
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
                return vi.hyphen_names
        lk_idx = name.indexOf 'lautakunta'
        if lk_idx >= 0
            prev_char = name[lk_idx-1]
            if prev_char != ' ' and prev_char != '-'
                hyphen = '-'
            else
                hyphen = ''

            name = name[0..lk_idx-1] + '&shy;' + name[lk_idx..]
        return name
    render: ->
        model = @model.toJSON()
        model.title = @format_title()
        model.icon = @model.get_icon()
        html = _.template @template, model
        @$el.addClass @model.get_category()
        @$el.attr 'href', @model.get_view_url()
        @$el.append html
        return @

class PolicymakerListView extends Backbone.View
    tagName: 'div'
    className: 'policymaker-list'

    render_pm_section: (list, heading, big, anchor) ->
        list = _.sortBy list, (m) -> m.get 'name'
        $container = @$el
        if heading
            $container.append $("<h2>#{heading}</h2>")
        row_idx = 0
        $row = $("<div class='row'></div>")
        if anchor
            $row.attr 'id', anchor
        for m in list
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
        @$el.empty()

        council = @collection.filter (m) -> m.get_category() == 'council'
        @render_pm_section council, null, true, 'council'

        gov = @collection.filter (m) -> m.get_category() == 'government'
        @render_pm_section gov, null, true, 'government'

        committees = @collection.filter (m) -> m.get_category() == 'committee'
        @render_pm_section committees, "Lautakunnat", false, 'committee'

        boards = @collection.filter (m) -> m.get_category() == 'board'
        @render_pm_section boards, "Johtokunnat", true, 'board'

        others = @collection.filter (m) -> m.get_category() == 'other'
        @render_pm_section others, "Muut", true, 'other'

class PolicymakerDetailsView extends Backbone.View
    tagName: 'div'
    className: 'policymaker-details'
    template: _.template $("#policymaker-details-template").html()

    initialize: ->
        @listenTo @model.meeting_list, 'reset', @_select_meeting
        @listenTo @model.meeting_list, 'reset', @render_meeting_list

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
            data = meeting.toJSON()
            if meeting.id == @selected_meeting.id
                data.is_selected = true
            else
                data.is_selected = false
            data.date_str = @format_date meeting.get('date')
            data.view_url = meeting.get_view_url()
            $li = $($.trim(template data))
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
        model.policymaker = @model.toJSON()

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

        @$el.find('.description-link').click (ev) =>
            ev.preventDefault()
            tab = @$el.find('.description-tab')
            if tab.hasClass 'active'
                return

            @$el.find('.tab-pane').hide().removeClass 'active'
            tab.fadeIn 100
            tab.addClass 'active'

        @$el.find('.meeting-link').click (ev) =>
            ev.preventDefault()
            tab = @$el.find('.meeting-details-tab')
            if tab.hasClass 'active'
                return

            @$el.find('.tab-pane').hide().removeClass 'active'
            tab.fadeIn 100
            tab.addClass 'active'

        @$el.find('.meeting-details-tab').fadeIn(100)

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
        content_el = $(".policymaker-content")
        content_el.empty()
        content_el.append list_view.$el

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

VIEW_BASE_URL = VIEW_URLS['policymaker-list']
Backbone.history.start {pushState: true, hashChange: false, root: VIEW_BASE_URL}
