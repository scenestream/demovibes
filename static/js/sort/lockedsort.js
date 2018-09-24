/*
    sortLocked
    -------------------

    This function sorts by locked / unlocked status.
*/

var sortLocked = fdTableSort.sortNumeric;

function sortLockedPrepareData(tdNode, innerText){
	// debug
	// console.log(tdNode.innerHTML);

	// indexOf version
	return tdNode.innerHTML.indexOf('<span style="display:none">u</span>');

  /*
	// regex version
	var regex = /<span[^>]*>u<\/span>/g;
	return tdNode.innerHTML.search(regex);
  */
}
