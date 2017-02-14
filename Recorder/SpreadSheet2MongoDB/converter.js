$( document ).ready(function() {
    console.log("ready!");
    //console.log(data);
    //var output = convertGestures(Window.gestures["all"]);

    //var output = convertMutations(Window.mutations["H001"]); //convert multi-handed mutation "H001"
    var output = convertMutations(Window.mutations["neMutations"], true);
    showItems(output);
});

function showItems(allItems) {
  console.log(allItems);
  console.log(allItems.length);
  //output all at once
  $("#jsonOutputArea").text(JSON.stringify(allItems, null, 2));
  //create easy to use list
  $.each(allItems, function( i, __items ) {
    $("#itemList").append("<li>"+i+": <textarea>"+JSON.stringify(__items, null, 2)+"</textarea></li>");
  });
};

//helper

function convertToID(prefix, number, length) {
  number = pad(number, length);
  if(prefix != null && prefix != "") {
    number = prefix + number;
  };
  return number;
};

function pad (str, max) {
  str = str.toString();
  return str.length < max ? pad("0" + str, max) : str;
}
