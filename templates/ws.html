<!DOCTYPE html>
<html>

<head>
  <style>
    h3 {
      margin-bottom: 0.2rem;
    }
  </style>
</head>

<body>
  <h2>Websocket Channel Monitor</h2>
  <hr />
  <h3>Websocket Operation</h3>
  <button id="connect-button" onclick="wsInstance.close();connect();">connect</button>
  <button id="disconnect-button" onclick="wsInstance.close();">disconnect</button><br> status: <span id="status-text">disconnect</span>
  <hr />
  <h3>Subscribe Channel</h3>
  <select name="channelName">
    <option value="">--channel--</option>
  </select>
  <button id="subscribe-button">subscribe</button>
  <table id="channelTable" border="1">
    <thead>
      <tr>
        <th>timestamp</th>
        <th>channel</th>
        <th>operation</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>
  <hr />
  <h3>Publish to Channel</h3>
  <select name="toPublishChannelName">
    <option value="">--channel--</option>
  </select>
  <br>
  <textarea name="toPublishMessage" rows=10 cols=50>{"foo":"bar"}</textarea>
  <br>
  <button id="publish-button">publish</button>
  <hr />
  <h3>Log <button onclick="clearLog()">clear</button></h3>
  <table id="logTable" border="1">
    <thead>
      <tr>
        <th>timestamp</th>
        <th>channel</th>
        <th>message</th>
      </tr>
    </thead>
    <tbody></tbody>
  </table>
  <script>
    const logTbody = document.querySelector("#logTable tbody");
    const channelTbody = document.querySelector("#channelTable tbody");

    const wsInstance = (function() {
      const obj = {
        set: function(ws) {
          this.instance = ws;
        },
        instance: null,
        close: function() {
          if (this.instance) {
            this.instance.close();
          }
          document.querySelector("#subscribe-button").setAttribute("disabled", "disabled");
          document.querySelector("#status-text").innerHTML = "disconnect";
        }
      };
      return obj;
    })();

    function appendLog(tbody, td1Text, td2Text, td3Text) {
      const tr = document.createElement("tr");
      const td1 = document.createElement("td");
      td1.innerHTML = td1Text;
      tr.appendChild(td1);

      const td2 = document.createElement("td");
      td2.innerHTML = td2Text;
      tr.appendChild(td2);

      const td3 = document.createElement("td");
      if (typeof td3Text === "string") {
        td3.innerHTML = td3Text;
      }
      else {
        td3.appendChild(td3Text);
      }
      tr.appendChild(td3);

      if (tbody.childNodes.length === 0) {
        tbody.appendChild(tr);
      }
      else {
        tbody.insertBefore(tr, tbody.childNodes[0]);
      }
    }

    function updateChannelList(channelNames) {
      ["channelName", "toPublishChannelName"].forEach(function(name) {
        const select = document.querySelector(`select[name=${name}]`);
        const options = select.querySelectorAll(`select[name=${name}] option`);
        for (let i = options.length - 1; i > 0; i--) {
          options[i].remove();
        }
        channelNames.forEach(function(channelName) {
          if (channelName !== "channelList") {
            const option = document.createElement("option");
            option.innerHTML = channelName;
            option.value = channelName;
            select.appendChild(option);
          }
        });
      });
    }

    function padding(input, scale = 2) {
      if (scale === 2) {
        if (input < 10) {
          return "0" + input
        }
        else {
          return input + ""
        }
      }
      else if (scale === 3) {
        if (input < 10) {
          return "00" + input
        }
        else if (input < 100) {
          return "0" + input
        }
        else {
          return input + ""
        }
      }
    }

    function connect() {
      const websocket = new WebSocket("wss://" + location.hostname + "/echo");
      wsInstance.set(websocket);
      websocket.addEventListener('open', function(event) {
        console.log('opened');
        document.querySelector("#subscribe-button").disabled = false;
        document.querySelector("#status-text").innerHTML = "connect";
        websocket.send(JSON.stringify({ open: true }));
      });
      websocket.addEventListener('close', function(event) {
        console.log('closed');
        const channels = document.querySelectorAll("#channelTable tbody tr")
        for (var i = 0; i < channels.length; i++) {
          channels[i].remove();
        }
      });
      websocket.addEventListener("message", function(event) {
        const data = JSON.parse(event.data)
        console.log(data)
        const date = new Date(data.timestamp)
        if (data.type === "subscribeStart") {
          const button = document.createElement("button");
          button.value = data.processId;
          button.innerHTML = "stop";
          button.id = data.processId;
          button.onclick = function() {
            websocket.send(JSON.stringify({ close: true, processId: data.processId }));
          };
          appendLog(
            channelTbody,
            padding(date.getMonth() + 1) +
            "/" + padding(date.getDate()) +
            " " + padding(date.getHours()) +
            ":" + padding(date.getMinutes()) +
            ":" + padding(date.getSeconds()) +
            "." + padding(date.getMilliseconds(), 3), data.channelName, button)
        }
        else if (data.type === "subscribeEnd") {
          document.querySelector("#" + data.processId).parentNode.parentNode.remove();
        }
        else {
          appendLog(
            logTbody,
            padding(date.getMonth() + 1) +
            "/" + padding(date.getDate()) +
            " " + padding(date.getHours()) +
            ":" + padding(date.getMinutes()) +
            ":" + padding(date.getSeconds()) +
            "." + padding(date.getMilliseconds(), 3), data.channelName, JSON.stringify(data.subscribed))
        }
        if (data.channelName === "channelList") {
          updateChannelList(data.subscribed)
        }
      });
      document.querySelector("#subscribe-button").onclick = function() {
        const channelName = document.querySelector("[name=channelName]").value;
        if (channelName) {
          websocket.send(JSON.stringify({ subscribe: true, channel: channelName }));
        }
      };
      document.querySelector("#publish-button").onclick = function() {
        const channelName = document.querySelector("[name=toPublishChannelName]").value;
        const message = document.querySelector("[name=toPublishMessage]").value;
        try{JSON.parse(message)}catch(e){
          alert("invalid json message")
          return false;
        }
        if (channelName) {
          websocket.send(JSON.stringify({ publish: true, channel: channelName, json: JSON.parse(message) }));
        }
      };
    }

    function clearLog() {
      const tbody = document.querySelector("#logTable tbody");
      while (tbody.firstChild) {
        tbody.removeChild(tbody.firstChild);
      }
    }
  </script>
</body>

</html>