function convertGestures(_data) {
  //get the header and delete it from the array
  var header = _data.shift();
  var gestures = [];

  //convert
  $.each(_data, function( i, line ) {
    //get each line
    var lineEntrys = [];
    $.each(line, function( attributeSlug,  attributeValue) {
      lineEntrys.push({"attrSlug":attributeSlug, "attrName":header[attributeSlug], "attrValue":attributeValue});
    });
    var gesture = structurizeGestures(lineEntrys);
    gestures.push(gesture);
    //return false; //<-- Abbruch bei Zeile 1
  });
  return gestures;
}

function structurizeGestures(_entrys) {
  //define Scheme for conversion
  var gesture = {};

  $.each(_entrys, function( i,  _entry) {
      if(_entry["attrName"] == "id") {
        gesture["id"] = convertToID("G",_entry["attrValue"],2);
      };
      //- slug raussuchen
      if(_entry["attrName"] == "slug") {
        gesture["slug"] = _entry["attrValue"];
      };
      //- name raussuchen
      if(_entry["attrName"] == "name") {
        gesture["name"] = _entry["attrValue"];
      };
      //- name raussuchen
      if(_entry["attrName"] == "isNesture") {
        if(_entry["attrValue"] == "N") {
          gesture["isNesture"] = true;
        }
      };
      //- name raussuchen
      if(_entry["attrName"] == "isGarbage") {
        if(_entry["attrValue"] == "Yes") {
          gesture["isGarbage"] = true;
        }
      };
  });

  return gesture;
};
