$( document ).ready(function() {
    console.log("ready!");
    //console.log(data);

    var mutations = convertData(data);

    //output all at once
    $("#jsonOutputArea").text(JSON.stringify(mutations, null, 2));
    //create easy to use list
    $.each(mutations, function( i, __mutation ) {
      $("#itemList").append("<li>"+i+": <textarea>"+JSON.stringify(__mutation, null, 2)+"</textarea></li>");
    });
});

function convertData(_data) {
  //get the header and delete it from the array
  var header = _data.shift();
  var mutations = {};

  //convert
  $.each(_data, function( i, line ) {
    //get each line
    var lineEntrys = [];
    $.each(line, function( attributeSlug,  attributeValue) {
      lineEntrys.push({"attrSlug":attributeSlug, "attrName":header[attributeSlug], "attrValue":attributeValue});
    });
    var mutation = structurize(lineEntrys);
    mutations["M"+mutation.id] = mutation;
    //return false; //<-- Abbruch bei Zeile 1
  });

  return mutations;
};

function structurize(_entrys) {

  //define Scheme for conversion
  var mutation = {};
  mutation["params"] = [];

  var activeHand = false;

  $.each(_entrys, function( i,  _entry) {
    //- id rausnehmen
    //TODO: die Synatax muss noch auf "Mxxx" geändert werden
    if(_entry["attrName"] == "id") {
      mutation["id"] = _entry["attrValue"];
    };
    //- slug zusammenfügen aus s[i]
    //TODO: die Syntax muss noch auf "[Hxxx][Gxx][aaaaaaabaaaba]" abgändert werden!
    if(_entry["attrName"] == "slug") {
      if(mutation.hasOwnProperty("slug")) {
        mutation.slug = mutation.slug + _entry["attrValue"];
      } else {
        mutation["slug"] = _entry["attrValue"];
      };
    };
    //- instruction raussuchen
    if(_entry["attrName"] == "instruction") {
      mutation["instruction"] = _entry["attrValue"];
    };

    //- aktive Hand aus activeHand bestimmen
    if(_entry["attrName"] == "hands.active") {
      activeHand = _entry["attrValue"];
      mutation["hands"] = {};
      mutation.hands[activeHand] = {};
    };
    //hands[active].instruction
    if(_entry["attrName"] == "hands[active].instruction") {
      mutation.hands[activeHand]["instruction"] = _entry["attrValue"];
    };

    //Gesture Daten zuordnen
    if(_entry["attrName"].indexOf("hands[active].gesture") != -1) {
      if(!mutation.hands[activeHand].hasOwnProperty("gesture")) {
        mutation.hands[activeHand]["gesture"] = {};
      };
      //TODO: die Syntax muss noch auf "Gxx" oder "Gxxx" geändert werden
      if(_entry["attrName"] == "hands[active].gesture.id") {
        mutation.hands[activeHand].gesture["id"] = _entry["attrValue"];
      };
      //kann auf "_.gesture.name" erweitert werden
    };

    //Host Daten zuordnen
    if(_entry["attrName"].indexOf("hands[active].host") != -1) {
      if(!mutation.hands[activeHand].hasOwnProperty("host")) {
        mutation.hands[activeHand]["host"] = {};
      };
      //add id
      //TODO: die Syntax muss noch auf "Hxxx" geändert werden
      if(_entry["attrName"] == "hands[active].host.id") {
        mutation.hands[activeHand].host["id"] = _entry["attrValue"];
      };
      //add name
      if(_entry["attrName"] == "hands[active].host.name") {
        mutation.hands[activeHand].host["name"] = _entry["attrValue"];
      };

      //Spot Daten zuordnen
      if(_entry["attrName"].indexOf("hands[active].host.spot") != -1) {
        if(!mutation.hands[activeHand].host.hasOwnProperty("spot")) {
          mutation.hands[activeHand].host["spot"] = {};
        };
        //add id
        if(_entry["attrName"] == "hands[active].host.spot.id") {
          mutation.hands[activeHand].host.spot["id"] = _entry["attrValue"];
        };
        //add name
        if(_entry["attrName"] == "hands[active].host.spot.name") {
          mutation.hands[activeHand].host.spot["name"] = _entry["attrValue"];
        };
      };

    };

    //- Params zuordnen
    if(_entry["attrSlug"].match(/^[m][a-zA-Z0-9]{1}/)) { //suche nach m[i] Syntax
      mutation.params.push(
        {"slug":_entry["attrSlug"], "label":_entry["attrName"], "value": _entry["attrValue"]}
      );
    };
  });
  //check
  return mutation;
};
