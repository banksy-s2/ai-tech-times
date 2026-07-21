(function(){
 if (!window.firebase || !window.__ART) return;
 firebase.initializeApp({"apiKey":"AIzaSyC3gYixsTTOb8TGgLwBEt7UplwClE_v00s","authDomain":"ai-tech-times.firebaseapp.com","projectId":"ai-tech-times"});
 var db = firebase.firestore();
 var A = window.__ART, ref = db.collection("likes").doc(A.id);
 var btn = document.getElementById("likebtn"), cnt = document.getElementById("likecount");
 ref.get().then(function(d){ cnt.textContent = d.exists ? (d.data().count || 0) : 0; }).catch(function(){});
 if (localStorage.getItem("liked:" + A.id)) btn.classList.add("liked");
 window.doLike = function(){
   if (localStorage.getItem("liked:" + A.id)) return;
   localStorage.setItem("liked:" + A.id, "1");
   btn.classList.add("liked");
   cnt.textContent = (parseInt(cnt.textContent || "0", 10) + 1);
   ref.set({count: firebase.firestore.FieldValue.increment(1), title: A.title, path: A.path, cat: A.cat}, {merge: true}).catch(function(){});
 };
})();