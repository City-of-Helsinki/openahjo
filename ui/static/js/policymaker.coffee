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
    #'Oivajk':
    #    hyphen_names: ['Henkilöstön kehittämispalvelut-liikelaitoksen jk']

class PolicymakerListNavView extends Backbone.View
    el: '.policymaker-nav'

    initialize: ->
        @collection.on 'reset', @render, @
        @active_category = null
    render: ->
        COMPONENTS = [
            {name: 'Kaupunginvaltuusto', category: 'council'}
            {name: 'Kaupunginhallitus', category: 'board'}
            {name: 'Lautakunnat', category: 'committee'}
            {name: 'Jaostot', category: 'board_division'}
            {name: 'Viranhaltijat', category: 'office_holder'}
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
    tagName: 'li'
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
        model.view_url = @model.get_view_url()
        org_hierarchy = [model.department, model.division, model.unit]
        model.org_hierarchy = (x for x in org_hierarchy when x).join ' / '
        html = _.template @template, model
        @$el.addClass @model.get_category()
        @$el.append html
        @$el.find('a.content').click (ev) ->
            if router.navigate_to_link ev.currentTarget
                ev.preventDefault()

        return @

class PolicymakerListView extends Backbone.View
    tagName: 'div'
    className: 'policymaker-list'

    render_pm_section: (list, heading, big, anchor) ->
        if anchor == 'office_holder'
            list = _.sortBy list, (m) ->
                dep = m.get 'department'
                if not dep
                    dep = '0'
                dep + ' ' + m.get('name')
        else
            list = _.sortBy list, (m) -> m.get 'name'
        $container = @$el
        if heading
            $container.append $("<h2>#{heading}</h2>")
        row_idx = 0
        $row = $("<ul class='row list-unstyled'></ul>")
        if anchor
            $row.attr 'id', anchor
        for m in list
            view = new PolicymakerListItemView {model: m}
            view.render()
            $el = view.$el
            if big
                $el.addClass 'col-md-12'
            else
                $el.addClass 'col-md-6 col-lg-6'
            $row.append view.$el

        $container.append $row

    render: ->
        @$el.empty()

        council = @collection.filter (m) -> m.get_category() == 'council'
        @render_pm_section council, null, true, 'council'

        gov = @collection.filter (m) -> m.get_category() == 'board'
        @render_pm_section gov, null, true, 'board'

        committees = @collection.filter (m) -> m.get_category() in ['committee', 'board_division']
        @render_pm_section committees, "Lautakunnat ja jaostot", false, 'committee'

        office_holders = @collection.filter (m) -> m.get_category() == 'office_holder'
        @render_pm_section office_holders, "Viranhaltijat", true, 'office_holder'

class PolicymakerDetailsView extends Backbone.View
    tagName: 'div'
    className: 'policymaker-details'
    template: _.template $("#policymaker-details-template").html()

    initialize: (opts) ->
        @policymaker = opts.policymaker
        if @policymaker
            @listenTo @policymaker.meeting_list, 'reset', @_select_meeting
            @listenTo @policymaker.meeting_list, 'reset', @render_meeting_list

    format_date: (date) ->
        m = moment date
        return m.format DATE_FORMAT

    generate_parent_tree: (org) ->
        FIXED_PARENTS =
            'hel:02100': 'hel:11010' # Kaupunginkanslia -> Kj
            'hel:02978': 'hel:11010' # Kaupunginhallituksen konsernijaosto -> Kj
            'hel:811000': 'hel:81000' # Sote -> Sotelk
            'hel:40000': 'hel:40200' # Opev -> OLK
            'hel:60111': 'hel:60100' # Kv -> Klk
            'hel:900VH1': 'hel:900' # Kaupunginhallituksen puheenjohtaja (VH) -> Khpj

        parents = [org]
        while org.parents.length > 0
            parent = org.parents[0]
            if org.parents.length > 1
                if not org.id of FIXED_PARENTS
                    console.error "Too many parents for #{org.name_fi}"
                else
                    p_id = FIXED_PARENTS[org.id]
                    for p in org.parents
                        if p.id == p_id
                            parent = p
                            break
            parents.push parent
            org = parent

        for org in parents
            org.css_class = switch org.type
                when 'office_holder' then 'officer'
                when 'department', 'unit', 'city' then 'office'
                when 'council', 'committee', 'board_division', 'board' then 'policymaker'
                else 'office'
            org.view_url = VIEW_URLS['policymaker-details'].replace 'ID', org.slug

        return parents.reverse()

    render: ->
        data = org: @model.toJSON()
        if @policymaker
            data.policymaker = @policymaker.toJSON()
        else
            data.policymaker = null
        data.parents = @generate_parent_tree data.org
        if @selected_meeting_id
            data.default_tab = 'meetings'
        else
            data.default_tab = 'description'
        html = @template data
        @$el.html html

        @$el.find('.description-link').click (ev) =>
            if router.navigate_to_link ev.currentTarget
                ev.preventDefault()

        @$el.find('.meeting-link').click (ev) =>
            ev.preventDefault()
            tab = @$el.find('.meeting-details-tab')
            if tab.hasClass 'active'
                return

            @$el.find('.tab-pane').hide().removeClass 'active'
            tab.fadeIn 100
            tab.addClass 'active'

        @$el.find('.policymaker-organisation a').click (ev) ->
            if router.navigate_to_link ev.currentTarget
                ev.preventDefault()
        @$el.find('.policy-breadcrumb a').click (ev) ->
            if router.navigate_to_link ev.currentTarget
                ev.preventDefault()

        return @

    render_meeting_list: ->
        list = @policymaker.meeting_list
        $list_el = @$el.find('.meeting-list').first()
        $list_el.empty()
        template = _.template $("#policymaker-meeting-list-item-template").html()
        list.each (meeting) =>
            data = meeting.toJSON()
            if @selected_meeting and meeting.id == @selected_meeting.id
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
        model.policymaker = @policymaker.toJSON()
        model.org = @model.toJSON()

        agenda_items = []
        meeting.agenda_item_list.each (ai) ->
            m = ai.toJSON()
            agenda_items.push m
        model.agenda_items = agenda_items

        meeting_list = @policymaker.meeting_list
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
        @$el.find('.meeting-details .tab-content .meeting-details-tab').remove()
        @$el.find('.meeting-details .tab-content').append $(html)

        @$el.find('.back-fwd a').click (ev) ->
            if router.navigate_to_link @
                ev.preventDefault()
        @$el.find('.policy-breadcrumb-navi a').click (ev) ->
            if router.navigate_to_link @
                ev.preventDefault()

        @$el.find('.meeting-details-tab').fadeIn(100)

    _select_meeting: ->
        if not @selected_meeting_id
            return

        meeting_list = @policymaker.meeting_list
        if @selected_meeting
            @stopListening @selected_meeting.agenda_item_list

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

        @listenTo meeting.agenda_item_list, 'reset', @render_meeting_details
        @selected_meeting = meeting
        meeting.fetch_agenda_items()

    select_meeting: (@selected_meeting_id) ->
        @policymaker.fetch_meetings()

policymaker_list = new PolicymakerList policymakers

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
        document.title = "Päättäjät | Päätökset | Helsingin kaupunki"
        list_view.render()
        content_el = $(".policymaker-content")
        content_el.empty()
        content_el.append list_view.$el

    pm_details: (slug, year, number) ->
        pm_matches = policymaker_list.filter (m) -> m.get('slug') == slug
        if pm_matches.length
            pm = pm_matches[0]
        else
            pm = null

        # We might have organization_json passed in from backend code.
        if organization_json? and organization_json.slug == slug
            org = new Organization organization_json
            org_promise = $.Deferred()
            org_promise.resolve()
        else
            if pm
                org_id = pm.get 'origin_id'
            else
                slug_map =
                    sotejo1: '82000'
                    sotejo2: '83000'
                    sotejo3: '84000'
                if slug in slug_map
                    org_id = slug_map[slug]
                else
                    org_id = slug
            # If not, we fetch the organization information.
            org = new Organization id: "hel:#{org_id}"
            org_promise = org.fetch
                data:
                    children: 'true'

        # Only render the view after the organization object has been
        # fetched from backend.
        org_promise.done ->
            #nav_view.set_category pm.get_category()
            $(".content-header-content > h1").html org.get('name_fi')
            document.title = "#{org.get 'name_fi'} | Päätökset | Helsingin kaupunki"
            details_view = new PolicymakerDetailsView model: org, policymaker: pm

            meeting_id = null
            if pm
                if year and number
                    meeting_id = "#{year}/#{number}"

            details_view.selected_meeting_id = meeting_id
            details_view.render()
            if pm
                details_view.select_meeting meeting_id
            $(".policymaker-content").empty()
            $(".policymaker-content").append details_view.$el

router = new PolicymakerRouter

VIEW_BASE_URL = VIEW_URLS['policymaker-list']
Backbone.history.start {pushState: true, hashChange: false, root: VIEW_BASE_URL}
