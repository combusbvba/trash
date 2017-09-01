window.onload = function() {
    console.log("window.onload");
    $(document).ready(function() {
        console.log("$(document).ready");
        rogerthat.callbacks.ready(onRogerthatReady);

        rogerthat.callbacks.backPressed(function() {
            console.log("BACK pressed");
            var activePage = $.mobile.activePage.attr('id');
            var newPage = null;
            if (activePage == null) {
            } else if (activePage == "overview") {
            } else if (activePage == "location-streets") {
                newPage = "overview";
            } else if (activePage == "location-housenr") {
                newPage = "location-streets";
            } else if (activePage == "notifications") {
                newPage = "overview";
            }

            if (newPage == null) {
                return false;
            }
            setTimeout(function() {
                $.mobile.changePage('#' + newPage);
            }, 100); // need to do this async
            return true; // we handled the back press
        });
    });
}; 

var currentLocationInfo = null;
var streets = {}
var HOUR = 60 * 60;
var DAY = 24 * HOUR;

var onRogerthatReady = function() {
    console.log("onRogerthatReady()");
    rogerthat.api.callbacks.resultReceived(onReceivedApiResult);
    rogerthat.callbacks.userDataUpdated(initOverview);

    $(document).on("click", ".current-location", function() {
        console.log("click .current-location");
        $(".set-location-error").hide();
        $("#location-streets ul").empty();
        var l = $('<li></li>');
        l.append(createLoadingDiv(Translations.LOADING_STREETS));
        $("#location-streets ul").append(l);
        
        rogerthat.api.call("trash.getStreets", "", "");
    });
    
    $(document).on("click", ".notifications-set", function() {
        console.log("click .notifications-set");
        initNotifications();
    });
    
    $(document).on("click", "#notifications-save", function() {
        console.log("click #notifications-save");
        
        var notifications = [];
        $("#notifications ul fieldset input[type=checkbox]:checked").each(function() {
            notifications.push(parseInt($(this).attr("notification-id")));
        });

        rogerthat.user.data.trash.notifications = notifications;
        rogerthat.user.put();
        
        var p = JSON.stringify({
            'notifications' : notifications,
        });
        rogerthat.api.call("trash.setNotifications", p, "");
    });
    
    $(document).on("click", ".location-street", function() {
        console.log("click .location-street");
        currentLocationInfo = {}
        currentLocationInfo.street = {}
        currentLocationInfo.street.number = parseInt($(this).attr("street_id"));
        currentLocationInfo.street.name = streets[currentLocationInfo.street.number];
        
        $("#location-housenr ul").empty();
        var l = $('<li></li>');
        l.append(createLoadingDiv(Translations.LOADING_HOUSE_NUMBERS));
        $("#location-housenr ul").append(l);
        
        var p = JSON.stringify({
            'streetnumber' : currentLocationInfo.street.number,
        });
        rogerthat.api.call("trash.getStreetNumbers", p, "");
    });
    
    $(document).on("click", ".location-housenr", function() {
        console.log("click .location-housenr");
        currentLocationInfo.house = {}
        currentLocationInfo.house.number = parseInt($(this).attr("house_nr"));
        currentLocationInfo.house.bus = $(this).attr("house_bus");
        
        setLocation();
    });
    
    initOverview();
};

var onReceivedApiResult = function(method, result, error, tag){
    console.log("onReceivedApiResult");
    console.log("method: " + method);
    console.log("result: " + result);
    console.log("error: " + error);

    if (result) {
        if (method == "trash.getStreets") {
            var r = JSON.parse(result);
            $.each(r, function (i, street) {
                streets[street.number] = street.name
            });
            
            var html = $.tmpl(streetTemplate, {
                streets : r
            });
            $("#location-streets ul").empty().append(html);
            
        } else if (method == "trash.getStreetNumbers") {
            var r = JSON.parse(result);
            var html = $.tmpl(houseTemplate, {
                houses : r
            });
            $("#location-housenr ul").empty().append(html);
            
        } else if (method == "trash.setLocation") {
            // do nothing the update of the user_data will stop the loading and goto the correct screen
        } else if (method == "trash.setNotifications") {
            // do nothing the user_data was put when sending the request
        }
    } else {
        if (method == "trash.setLocation") {
            $(".set-location-error").show();
            $(".set-location-error p").text(error);
            
            var activePage = $.mobile.activePage.attr('id');
            if (activePage != "overview") {
                $.mobile.loading('hide');
                setTimeout(function() {
                    $.mobile.changePage('#overview');
                }, 100); // need to do this async
            }
        }
    }
};

//var language = window.navigator.languages ? window.navigator.languages[0] : null;
//language = language || window.navigator.language || window.navigator.browserLanguage || window.navigator.userLanguage;
var language = "nl";
moment.locale(language);

var parseDateToEventDate = function(d) {
    var momentTrans = moment(d).format("dddd LL");
    return momentTrans;
};

var isSameDay = function(a, b) {
    return (a.getDate() == b.getDate()
        && a.getMonth() == b.getMonth()
        && a.getFullYear() == b.getFullYear())
};

var filter = function (array, callback) {
    var result = [];
    for ( var index in array ) {
        if (callback(array[index], index)) {
            result.push(array[index]);
        }
    }
    return result;
};

var createLoadingDiv = function(txt) {
    var d = $('<div style="text-align: center;"></div>');
    var i = $('<img src="jquery/images/ajax-loader.gif" style="height: 20px;width: 20px;">')
    d.append(i);
    var t = $('<p></p>').text(txt);
    d.append(t);
    return d;
};

var initOverview = function() {
    console.log("initOverview()");
    
    if(rogerthat.user.data.trash == undefined) {
        rogerthat.user.data.trash = {};
    }
    
    if (rogerthat.user.data.trash.address == undefined) {
        $(".current-location a").text(Translations.NO_LOCATION_SET);
    } else {
        $(".current-location a").text(rogerthat.user.data.trash.address);
        $(".notifications-set").show();
        $(".collections").show();
        
        var now = (new Date().getTime()) / 1000;
        var checkdate = now - DAY;
        var collections = filter(rogerthat.user.data.trash.collections, function (collection, i) {
            if (collection.epoch < checkdate) {
                return false
            }
            return true;
        });
        
        collections.sort(function(col1, col2) {
            return col1.epoch - col2.epoch;
        });
        
        var previousDate = null;
        var collectionsForDay = [];
        var days = [];
        $.each(collections, function (i, collection) {
            var d = new Date(collection.year, collection.month -1, collection.day);
            
            if (previousDate != null && !isSameDay(previousDate, d)) {
                if ( collectionsForDay.length > 0 ) {
                    days.push({"date": parseDateToEventDate(previousDate), "collections": collectionsForDay});
                    collectionsForDay = [];
                }
            }
            previousDate = d;
            if (collection.activity.number == 7) {
                collection.activity.image_url = "images/grofvuil.png";
            } else if (collection.activity.number == 21) {
                collection.activity.image_url = "images/huisvuil.png";
            } else if (collection.activity.number == 23) {
                collection.activity.image_url = "images/kerstboom.png";
            } else if (collection.activity.number == 27) {
                collection.activity.image_url = "images/papier.png";
            } else if (collection.activity.number == 28) {
                collection.activity.image_url = "images/pmd.png";
            } else if (collection.activity.number == 29) {
                collection.activity.image_url = "images/tuin.png";
            } else if (collection.activity.number == 30) {
                collection.activity.image_url = "images/textiel.png";
            } else {
                collection.activity.image_url = "images/unknown.png";
            }
            collectionsForDay.push(collection);
        });
        if ( collectionsForDay.length > 0 ) {
            days.push({"date": parseDateToEventDate(previousDate), "collections": collectionsForDay});
        }
        
        var html = $.tmpl(collectionTemplate, {
            days : days
        });
        $(".collections ul").empty().append(html);
        
        var activePage = $.mobile.activePage.attr('id');
        if (activePage != "overview") {
            $.mobile.loading('hide');
            setTimeout(function() {
                $.mobile.changePage('#overview');
            }, 100); // need to do this async
            
        }
    }
};

var initNotifications = function() {
    $("#notifications ul fieldset").empty();
    
    if(rogerthat.user.data.trash == undefined) {
        rogerthat.user.data.trash = {};
    }
    if (rogerthat.user.data.trash.notifications == undefined) {
        rogerthat.user.data.trash.notifications = [];
    }
    if (rogerthat.user.data.trash.notification_types == undefined) {
        rogerthat.user.data.trash.notification_types = [];
    }

    $.each(rogerthat.user.data.trash.notification_types, function (i, notification_type) {
        var input =  $('<input class="custom" type="checkbox">');
        input.prop("name", "notification-checkbox-" + notification_type.number);
        input.prop("id", "notification-checkbox-" + notification_type.number);

        var disabledFilter = $.inArray(notification_type.number, rogerthat.user.data.trash.notifications);
        input.prop('checked', disabledFilter >= 0);
        input.attr("notification-id", notification_type.number);
        $("#notifications ul fieldset").append(input);

        var label =  $('<label></label>');
        label.text(notification_type.name);
        label.prop("for", "notification-checkbox-" + notification_type.number);
        label.attr("notification-id", notification_type.number);
        $("#notifications ul fieldset").append(label);
    });
    $('#notifications').trigger('create');
};

var setLocation = function() {
    $.mobile.loading( 'show', {
        text: Translations.SETTING_UP_YOUR_CALENDAR,
        textVisible: true,
        theme: 'a',
        html: ""
    });
    
    var p = JSON.stringify({
        'info' : currentLocationInfo,
    });
    rogerthat.api.call("trash.setLocation", p, "");
};

var streetTemplate = '{{each(i, s) streets}}'
    + '<li class="location-street" street_id="${s.number}" onclick="">'
    + '<a href="#location-housenr" data-transition="slide" class="ui-btn ui-btn-icon-right ui-icon-carat-r">${s.name}</a>'
    + '</li>'
    + '{{/each}}';

var houseTemplate = '{{each(i, h) houses}}'
    + '<li class="location-housenr" house_nr="${h.number}" house_bus="${h.bus}" onclick="">'
    + '<a href="#" data-transition="slide" class="ui-btn ui-btn-icon-right ui-icon-carat-r">${h.number}${h.bus}</a>'
    + '</li>'
    + '{{/each}}';

var collectionTemplate = '{{each(i, d) days}}'
    + '<li data-role="list-divider" role="heading" class="ui-li ui-li-divider ui-bar-a ui-li-has-count">'
    + '${d.date} <span class="ui-li-count ui-btn-up-c ui-btn-corner-all">${d.collections.length}</span>'
    + '</li>'
    + '{{each(i, c) d.collections}}'
    + '<li>'
    + '<div class="ui-btn-inner ui-li">'
    + '<div class="ui-btn-text">'
    + '<div style="width: 30px; height: 30px; margin: 5px; position: relative;">'
    + '<img src="${c.activity.image_url}" alt="${c.activity.name}" class="ui-li-icon ui-corner-none ui-li-thumb" style="max-height: 100%;  max-width: 100%; width: auto; height: auto; position: absolute; top: 0; bottom: 0; left: 0; right: 0; margin: auto;">'
    + '<p style="margin-left: 40px; font-size: 13px; line-height: 14px; position: absolute;">${c.activity.name}</p>'
    + '</div>'
    + '</div>'
    + '</div>'
    + '</li>'
    + '{{/each}}'
    + '{{/each}}';

