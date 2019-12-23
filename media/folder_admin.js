var userPermTableId = "user_perm_formset_table";
var userPermTotalFormId = "id_user_perm-TOTAL_FORMS";
var groupPermTableId = "group_perm_formset_table";
var groupPermTotalFormId = "id_group_perm-TOTAL_FORMS";

var numUserPerms = 0;
var numGroupPerms = 0;

function confirmDelete(folderName) {
    var r=confirm("Are you sure you want to delete " + folderName);
    if (r==true) {
        post(Urls.deleteFolder(folderName));
    }
}

function replaceAttr(elem, attrName, rowId) {
    var val = elem.attr(attrName);
    if (val != null) {
        let newVal = val.replace(/([a-zA-Z_-]+)(\d+)(.*)/, "$1" + rowId + "$3");
        console.log('newVal = ' + newVal);
//        newVal = val.replace(/(\w+-)(\d+|(__prefix__))(-\w+)/, "$1" + rowId + "$4" );
        elem.attr(attrName, newVal);
    }
}

/*
function updateFormsetIds() {
    var userRowId = 0;
    var groupRowId = 0;
    $('#permissionTable tr').each(function() {
        var hasUserInput = false;
        var hasGroupInput = false;
        $(this).find("td :input").each(function() {
	    var name = $(this).attr('name');
	    if (name != null) {
	        if (name.startsWith(userPermFormPrefix)) {
	            hasUserInput = true;
                    replaceAttr($(this), 'name', userRowId);
                    replaceAttr($(this), 'id', userRowId);
	        } else if (name.startsWith(groupPermFormPrefix)) {
	            hasGroupInput = true;
                    replaceAttr($(this), 'name', groupRowId);
                    replaceAttr($(this), 'id', groupRowId);
	        }
	    }

        });

        if (hasUserInput) {
            userRowId++;
        } else if (hasGroupInput) {
	    groupRowId++;
	}
    });
    
    $('#id_' + userPermFormPrefix + '-TOTAL_FORMS').val(userRowId);
    $('#id_' + groupPermFormPrefix + '-TOTAL_FORMS').val(groupRowId);
}
*/

function addRow(tableId, row, index) {
    row.each(function() {
        $(this).find(":input").each(function() {
            replaceAttr($(this), 'name', index);
            replaceAttr($(this), 'id', index);
        });
    });

    var tbody = $('#' + tableId + " tbody");
    tbody.append(row);
}

function addUserPermRow() {
    addRow(userPermTableId, emptyUserPerm.clone(), numUserPerms);
    numUserPerms++;
    $('#' + userPermTotalFormId).val(numUserPerms);
}

function addGroupPermRow() {
    addRow(groupPermTableId, emptyGroupPerm.clone(), numGroupPerms);
    numGroupPerms++;
    $('#' + groupPermTotalFormId).val(numGroupPerms);
}

$(document).ready(function() {
    var emptyUserPerm = $('#' + userPermTableId + ' tr:last');
    var regexp = /(id_)?[a-zA-Z_]+-(\d+).*/;

    if (emptyUserPerm.find('select:first').val() == "") {
        emptyUserPerm.remove();
        let match = regexp.exec(emptyUserPerm.find('input').attr('name'))
        numUserPerms = parseInt(match[2]);
    } else {
        //var name = parseInt($('#' + userPermTableId + ' tr:last').find('input:first').attr('name'));
        let match = regexp.exec(emptyUserPerm.find('input').attr('name'))
        numUserPerms = parseInt(match[2]) + 1;
    }


    var emptyGroupPerm = $('#' + groupPermTableId + ' tr:last');

    if (emptyGroupPerm.find('select:first').val() == "") {
        emptyGroupPerm.remove();
        let match = regexp.exec(emptyGroupPerm.find('input').attr('name'))
        numGroupPerms = parseInt(match[2]);
    } else {
        //var name = parseInt($('#' + groupPermTableId + ' tr:last').find('input:first').attr('name'));
        let match = regexp.exec(emptyGroupPerm.find('input').attr('name'))
        numGroupPerms = parseInt(match[2]) + 1;
    }


    $('#' + userPermTotalFormId).val(numUserPerms);
    $('#' + groupPermTotalFormId).val(numGroupPerms);
});
