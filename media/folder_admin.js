	function confirmDelete(folderName) {
                var r=confirm("Are you sure you want to delete " + folderName);
                if (r==true) {
                        window.location = baseUrl + "folderAdminAction/?action=deleteFolder&name=" + folderName;
                }
        }

        function writeClicked(writeFieldId, readFieldId) {
                var writeBox = document.getElementById(writeFieldId);
                var readBox = document.getElementById(readFieldId);

                if (writeBox.checked) {
                        readBox.checked = true;
                        readBox.disabled = true;
                } else {
                        readBox.disabled = false;
                }
        }

	function deleteClicked(deleteFieldId, writeFieldId, readFieldId) {
                var deleteBox = document.getElementById(deleteFieldId);
                var writeBox = document.getElementById(writeFieldId);
                var readBox = document.getElementById(readFieldId);

                if (deleteBox.checked) {
                        readBox.checked = true;
                        readBox.disabled = true;

                        writeBox.checked = true;
                        writeBox.disabled = true;
                } else {
                        readBox.disabled = false;
                        writeBox.disabled = false;
                }

                writeClicked(writeFieldId, readFieldId);
        }

	function addRow(tableID, userOrGroupId, userOrGroup) {
        var table = document.getElementById(tableID);
        var userOrGroupName = document.getElementById(userOrGroupId).value;

        var rowCount = table.rows.length;
        var row = table.insertRow(rowCount);

        var cell1 = row.insertCell(0);

        if (userOrGroup == "group") {
                cell1.innerHTML = "<img src=\"" + mediaUrl + "User-Group-icon.png\"> " + userOrGroupName;
        } else {
                cell1.innerHTML = "<img src=\"" + mediaUrl + "Administrator-icon.png\"> " + userOrGroupName;
        }

        var cell2 = row.insertCell(1);
        var element2 = document.createElement("input");
        element2.type="checkbox";
        element2.name = userOrGroup + "-" + userOrGroupName + "-read";
        element2.id = userOrGroup + "-" + userOrGroupName + "-read";
        cell2.appendChild(element2);

        var cell3 = row.insertCell(2);
        var element3 = document.createElement("input");
        element3.type="checkbox";
        element3.name="write";
        element3.name = userOrGroup + "-" + userOrGroupName + "-write";
        element3.id = userOrGroup + "-" + userOrGroupName + "-write";
        element3.onclick=function(){writeClicked(element3.id, element2.id);};
        cell3.appendChild(element3);

        var cell4 = row.insertCell(3);
        var element4 = document.createElement("input");
        element4.type="checkbox";
        element4.name="delete";
	element4.name = userOrGroup + "-" + userOrGroupName + "-delete";
        element4.id = userOrGroup + "-" + userOrGroupName + "-delete";
        element4.onclick=function(){deleteClicked(element4.id, element3.id, element2.id);};
        cell4.appendChild(element4);
    }

        function showDialog(id) {
                var el = document.getElementById(id);
                el.style.visibility = "visible";
        }

        function hideDialog(id) {
                var el = document.getElementById(id);
                el.style.visibility = "hidden";
        }
