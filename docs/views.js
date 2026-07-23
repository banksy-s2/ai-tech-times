(function(){
 try{
  var id = location.pathname.replace(/[^a-zA-Z0-9\-_.]/g, "_").replace(/^_+|_+$/g, "") || "home";
  // JST日付: UTCに9時間を足してISO文字列のUTC日付部を読む(閲覧者のタイムゾーンに依存しない)
  var d = new Date(Date.now() + 9*3600*1000).toISOString().slice(0,10).replace(/-/g, "");
  var k = "v:" + d + ":" + id;
  if (sessionStorage.getItem(k)) return;  // 同一セッション内の再読込は数えない
  sessionStorage.setItem(k, "1");
  var doc = "projects/ai-tech-times/databases/(default)/documents/views/" + d;
  fetch("https://firestore.googleapis.com/v1/projects/ai-tech-times/databases/(default)/documents:commit?key=AIzaSyC3gYixsTTOb8TGgLwBEt7UplwClE_v00s", {
    method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({writes: [{transform: {document: doc, fieldTransforms: [
      {fieldPath: "total", increment: {integerValue: "1"}},
      {fieldPath: "pages.`" + id + "`", increment: {integerValue: "1"}}
    ]}}]})
  }).catch(function(){});
 }catch(e){}
})();