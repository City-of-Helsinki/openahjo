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
    get_view_url: ->
        return VIEW_URLS['issue-details'].replace 'ID', @get 'slug'

class @IssueList extends Backbone.Tastypie.Collection
    urlRoot: API_PREFIX + 'v1/issue/'
    model: Issue

class @IssueSearchList extends Backbone.Tastypie.Collection
    urlRoot: API_PREFIX + 'v1/issue/search/'
    model: Issue

    set_filter: (type, val) ->
        if type == 'text'
            filter_name = 'q'
        else if type in ['category', 'bbox', 'policymaker']
            filter_name = type
        else
            throw "Unknown filter type: #{type}"
        if not val
            if filter_name of @filters
                delete @filters[filter_name]
        else
            @filters[filter_name] = val

class @AgendaItem extends Backbone.Tastypie.Model

class @AgendaItemList extends Backbone.Tastypie.Collection
    urlRoot: API_PREFIX + 'v1/agenda_item/'
    model: AgendaItem

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
