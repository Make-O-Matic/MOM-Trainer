function convertAllMutation() {
  var allMutations = [];
  var data = Window.mutations;
  console.log(data);
  //Alle Mutations umwandeln

  $.each(data, function( hostId, __mutationExportData) {
    console.log(hostId);
    var output = convertMutations(__mutationExportData);
    console.log(output);
    allMutations = allMutations.concat(output);
  });
  return allMutations;
};

function convertMutations(_data, isNEMutationSyntax) {
  //get the header and delete it from the array
  var header = _data.shift();
  var __mutations = [];

  //convert
  $.each(_data, function( i, line ) {
    //get each line
    var lineEntrys = [];
    $.each(line, function( attributeSlug,  attributeValue) {
      lineEntrys.push({"attrSlug":attributeSlug, "attrName":header[attributeSlug], "attrValue":attributeValue});
    });
    if(isNEMutationSyntax == true) {
      var mutation = structurizeNE_Mutations(lineEntrys);
    } else {
      var mutation = structurizeMutations(lineEntrys);
    };
    __mutations.push(mutation);
    //return false; //<-- Abbruch bei Zeile 1
  });

  if(isNEMutationSyntax != true) {
    var ArrayLength = __mutations.length;

    //find two handed mutations and merge them
    for (var i = 0; i < __mutations.length; i++) {
      for (var j = i+1; j < __mutations.length; j++) {
        //console.log(__mutations[i]["id"] + " ? " + __mutations[j]["id"])
        if(__mutations[i]["id"].indexOf(__mutations[j]["id"]) != -1 || __mutations[j]["id"].indexOf(__mutations[i]["id"]) != -1) {
          console.log("found duplicates for " + __mutations[i].id);
          //merge duplicates
          var __mutationPrimary;
          var __mutationSecondary;
          //define important dataset
          if(__mutations[i].id.indexOf("_")) {
            __mutationPrimary = __mutations[i];
            __mutationSecondary = __mutations[j];
          } else if(__mutations[j].id.indexOf("_")) {
            __mutationPrimary = __mutations[j];
            __mutationSecondary = __mutations[i];
          } else {
            console.log("could not identify main dataset");
          }
          //slug
          __mutationPrimary.slug = __mutationPrimary.slug + "-" + __mutationSecondary.slug;
          //hands
          if(__mutationPrimary["hands"].hasOwnProperty("right") && __mutationSecondary["hands"].hasOwnProperty("right")) {
            console.log("can not merge same hands[right]");
          };
          if(__mutationPrimary["hands"].hasOwnProperty("left") && __mutationSecondary["hands"].hasOwnProperty("left")) {
            console.log("can not merge same hands[left]");
          };
          if(__mutationPrimary["hands"].hasOwnProperty("right") && __mutationSecondary["hands"].hasOwnProperty("left")) {
            //merge left Hand
            __mutationPrimary.hands["left"] = __mutationSecondary.hands["left"];
          };
          if(__mutationPrimary["hands"].hasOwnProperty("left") && __mutationSecondary["hands"].hasOwnProperty("right")) {
            //merge left Hand
            __mutationPrimary.hands["right"] = __mutationSecondary.hands["right"];
          };
          //delete data of __mutationSecondary from Array
          __mutations.splice(j, 1);
          ArrayLength = __mutations.length; //reset Array length
        }
      };
    };
  }
  return __mutations;
};

function structurizeNE_Mutations(_entrys) {
  //structurizes Mutations in another file format
  var mutation = {};

  //fields:
  //mutation.id, mutation.slug, mutation.instruction,
  //mutation.hands.right.instruction, mutation.hands.right.host.id, mutation.hands.right.host.name, mutation.hands.right.gesture.id
  //mutation.hands.left.instruction, mutation.hands.left.host.id, mutation.hands.left.host.name, mutation.hands.left.gesture.id

  $.each(_entrys, function( i,  _entry) {
    console.log(_entry["attrName"]);
    //mutation.id
    if(_entry["attrName"] == "id") {
      mutation["id"] = convertToID("M",_entry["attrValue"],3);
    };
    //mutation.slug
    if(_entry["attrName"] == "slug") {
      mutation["slug"] = _entry["attrValue"];
    };
    //mutation.instruction
    if(_entry["attrName"] == "instruction") {
      mutation["slug"] = _entry["attrValue"];
    };
    //hands
    //mutation.hands.right.instruction
    if(_entry["attrName"].indexOf("hands") != -1) {
      if(!mutation.hasOwnProperty("hands")) {
        mutation["hands"] = {};
      };
      //right hand
      if(_entry["attrName"].indexOf("hands.right") != -1) {
          if(!mutation.hands.hasOwnProperty("right")) {
            mutation.hands["right"] = {};
          };
          //mutation.hands.right.instruction
          if(_entry["attrName"] == "hands.right.instruction") {
              mutation.hands.right["instruction"] = _entry["attrValue"];
          };
          //mutation.hands.right.host
          if(_entry["attrName"].indexOf("hands.right.host") != -1) {
              if(!mutation.hands.right.hasOwnProperty("host")) {
                mutation.hands.right["host"] = {};
              };
              if(_entry["attrName"] == "hands.right.host.id") {
                mutation.hands.right.host["id"] = _entry["attrValue"];
              };
              if(_entry["attrName"] == "hands.right.host.name") {
                mutation.hands.right.host["name"] = _entry["attrValue"];
              };
          };
          //mutation.hands.right.gesture
          if(_entry["attrName"].indexOf("hands.right.gesture") != -1) {
              if(!mutation.hands.right.hasOwnProperty("gesture")) {
                mutation.hands.right["gesture"] = {};
              };
              if(_entry["attrName"] == "hands.right.gesture.id") {
                mutation.hands.right.gesture["id"] = _entry["attrValue"];
              };
              //...
          };
      };
      //left hand
      if(_entry["attrName"].indexOf("hands.left") != -1) {
          if(!mutation.hands.hasOwnProperty("left")) {
            mutation.hands["left"] = {};
          };
          //mutation.hands.right.instruction
          if(_entry["attrName"] == "hands.left.instruction") {
              mutation.hands.left["instruction"] = _entry["attrValue"];
          };
          //mutation.hands.right.host
          if(_entry["attrName"].indexOf("hands.left.host") != -1) {
              if(!mutation.hands.left.hasOwnProperty("host")) {
                mutation.hands.left["host"] = {};
              };
              if(_entry["attrName"] == "hands.left.host.id") {
                mutation.hands.left.host["id"] = _entry["attrValue"];
              };
              if(_entry["attrName"] == "hands.left.host.name") {
                mutation.hands.left.host["name"] = _entry["attrValue"];
              };
          };
          //mutation.hands.right.gesture
          if(_entry["attrName"].indexOf("hands.left.gesture") != -1) {
              if(!mutation.hands.left.hasOwnProperty("gesture")) {
                mutation.hands.left["gesture"] = {};
              };
              if(_entry["attrName"] == "hands.left.gesture.id") {
                mutation.hands.left.gesture["id"] = _entry["attrValue"];
              };
              //...
          };
      };
    };
  });

  return mutation;
};

function structurizeMutations(_entrys) {
  //console.log(_entrys);

  //define Scheme for conversion
  var mutation = {};
  mutation["params"] = [];

  var activeHand = false;

  $.each(_entrys, function( i,  _entry) {
    //console.log(_entry["attrName"]);
    //- id rausnehmen
    //TODO: die Synatax muss noch auf "Mxxx" geändert werden
    if(_entry["attrName"] == "id") {
      mutation["id"] = convertToID("M",_entry["attrValue"],3);
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
        mutation.hands[activeHand].gesture["id"] = convertToID("G",_entry["attrValue"],2);
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
        mutation.hands[activeHand].host["id"] = convertToID("H",_entry["attrValue"],3);
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

    //- slug zusammenfügen aus s[i]
    //TODO: die Syntax muss noch auf "[Hxxx][Gxx][aaaaaaabaaaba]" abgändert werden! <-- lasse ich mal als [aaaaaaabaaaba]
    if(_entry["attrName"] == "slug") {
      if(mutation.hasOwnProperty("slug")) {
        mutation.slug = mutation.slug + _entry["attrValue"];
      } else {
        mutation["slug"] = _entry["attrValue"];
      };
    };

    //- Params zuordnen
    // regex tested with - http://regexr.com/
    if(_entry["attrSlug"].match(/^[m]{1}[0-9]{1,2}/)) { //suche nach m[i] Syntax
      mutation.params.push(
        {"slug":_entry["attrSlug"], "label":_entry["attrName"], "value": _entry["attrValue"]}
      );
    };
  });
  //check
  return mutation;
};
