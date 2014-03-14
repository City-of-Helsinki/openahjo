class @Category extends Backbone.Tastypie.Model

class @CategoryList extends Backbone.Tastypie.Collection
    urlRoot: API_PREFIX + 'v1/category'
    model: Category
    comparator: (cat) -> return "#{cat.get 'level'} #{cat.get 'origin_id'}"

    reset: (models, options) ->
        super models, options
        @each @find_children

    find_children: (cat) =>
        cat.children = @get_children cat

    get_children: (parent) ->
        return @filter (m) -> return m.get('parent') == parent.id

class @Issue extends Backbone.Tastypie.Model
    initialize: ->
        @agenda_item_list = new AgendaItemList
        @agenda_item_list.filters['issue'] = @get 'id'
        @agenda_item_list.filters['limit'] = 1000

    fetch_agenda_items: ->
        if @agenda_item_list.length
            @agenda_item_list.trigger 'reset'
            return
        @agenda_item_list.fetch reset: true

    get_view_url: ->
        return VIEW_URLS['issue-details'].replace 'ID', @get 'slug'

class @IssueList extends Backbone.Tastypie.Collection
    urlRoot: API_PREFIX + 'v1/issue/'
    model: Issue

class @IssueSearchList extends IssueList
    urlRoot: API_PREFIX + 'v1/issue/search/'

    set_filter: (type, val) ->
        filter_name = type
        if not val
            if filter_name of @filters
                delete @filters[filter_name]
        else
            @filters[filter_name] = val

class @AgendaItem extends Backbone.Tastypie.Model
    get_slug: (pm_list) ->
        meeting = @get 'meeting'
        pm = pm_list.get meeting.policymaker
        slug = "#{pm.get 'slug'}-#{meeting.year}-#{meeting.number}"
        return slug
    get_view_url: (issue, pm_list) ->
        slug = @get_slug pm_list
        return issue.get_view_url() + slug + '/'
    has_non_public_attachments: ->
        for att in @get 'attachments'
            if not att.public
                return true
        return false

class @AgendaItemList extends Backbone.Tastypie.Collection
    urlRoot: API_PREFIX + 'v1/agenda_item/'
    model: AgendaItem

    comparator: (ai1, ai2) ->
        string_diff = (s1, s2) ->
            if s1 < s2
                return -1
            if s1 == s2
                return 0
            return 1
        diff = string_diff ai1.get('meeting').date, ai2.get('meeting').date
        if diff == 0
            return ai1.get('index') - ai2.get('index')
        return -diff

    find_by_slug: (slug, pm_list) ->
        parts = slug.split('-')
        pm_slug = parts[0]
        year = parseInt parts[1]
        number = parseInt parts[2]
        pm = pm_list.findWhere slug: pm_slug
        ai = @find (ai) ->
            meeting = ai.get 'meeting'
            if meeting.policymaker != pm.id
                return false
            if meeting.year != year or meeting.number != number
                return false
            return true

class @Meeting extends Backbone.Tastypie.Model
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

class @MeetingList extends Backbone.Tastypie.Collection
    urlRoot: API_PREFIX + 'v1/meeting/'
    model: Meeting

    initialize: (models, opts)->
        @policymaker_list = opts.policymaker_list

POLICYMAKERS =
    'Aslk': icon: 'home'
    'Asuntk': icon: 'home'
    'Zoojk': icon: 'bug'
    'Oivajk': icon: 'group'
    'Koja': icon: 'briefcase'
    'Sote': icon: 'medkit'
    'Khs': icon: 'legal'
    'Museojk': icon: 'asterisk'
    'Kvsto': icon: 'microphone'
    'Kslk': icon: 'eraser'
    'Kvlk': icon: 'ticket'
    'Klk': icon: 'building-o'
    'Kklk': icon: 'picture'
    'HKLjk': icon: 'road'
    'LILK': icon: 'trophy'
    'Nlk': icon: 'smile'
    'SKJ': icon: 'pencil'
    'OLK': icon: 'pencil'
    'Palmiajk': icon: 'leaf'
    'PELK': icon: 'fire-extinguisher'
    'Sotelk': icon: 'medkit'
    'Soslk': icon: 'medkit'
    'Stojk': icon: 'book'
    'Taimujk': icon: 'asterisk'
    'Talpajk': icon: 'euro'
    'Talk': icon: 'eye-open'
    'Tija': icon: 'laptop'
    'Tplk': icon: 'cog'
    'Tervlk': icon: 'medkit'
    'Vakalk': icon: 'smile'
    'Ytlk': icon: 'wrench'
    'Ylk': icon: 'leaf'

class @Policymaker extends Backbone.Tastypie.Model
    initialize: ->
        @meeting_list = new MeetingList null, policymaker_list: @collection
        @meeting_list.filters['policymaker'] = @get 'id'
        @meeting_list.filters['limit'] = 1000

    get_view_url: ->
        return VIEW_URLS['policymaker-details'].replace 'ID', @get('slug')
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

    get_icon: ->
        pm_info = POLICYMAKERS[@get 'abbreviation']
        if not pm_info
            return null
        return pm_info.icon

    fetch_meetings: ->
        if @meeting_list.length
            @meeting_list.trigger 'reset'
            return
        @meeting_list.fetch reset: true

class @PolicymakerList extends Backbone.Tastypie.Collection
    urlRoot: API_PREFIX + 'v1/policymaker/'
    model: Policymaker

    comparator: (pm) ->
        cat = pm.get_category()
        PRIORITIES =
            'council': 0
            'government': 1
            'committee': 2
            'board': 2
            'other': 2
        return "#{PRIORITIES[cat]} #{pm.get 'name'}"

class @District extends Backbone.Tastypie.Model

class @DistrictList extends Backbone.Tastypie.Collection
    urlRoot: API_PREFIX + 'v1/district'
    model: District
