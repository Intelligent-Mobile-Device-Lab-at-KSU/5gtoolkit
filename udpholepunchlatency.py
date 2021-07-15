var udp = require('dgram');

// --------------------creating a udp server --------------------
var totbytes = 0;
// creating a udp server
var server = udp.createSocket('udp4');

// emits when any error occurs
server.on('error',function(error){
  console.log('Error: ' + error);
  server.close();
});
var tic,start;

// emits on new datagram msg
server.on('message',function(msg,info){
  //console.log('Data received from client : ' + msg.toString());
  //console.log('Received %d bytes from %s:%d\n',msg.length, info.address, info.port);
    tic = Date.now();
    totbytes+=msg.length;
    if(totbytes==1){start=tic;}
server.send(Buffer.from('0'),info.port,info.address,function(error){
  
  if(error){
    server.close();
  }else{
    totbytes++;
    //console.log('Data sent !!!');
  }
});

});

//emits when socket is ready and listening for datagram msgs
server.on('listening',function(){
  var address = server.address();
  var port = address.port;
  var family = address.family;
  var ipaddr = address.address;
  console.log('Server is listening at port' + port);
  console.log('Server ip :' + ipaddr);
  console.log('Server is IP4/IP6 : ' + family);
});

//emits after the socket is closed using socket.close();
server.on('close',function(){
  console.log('Socket is closed! Rx (bytes): ');
  console.log(totbytes.toString());
});

function checkTime(){
  console.log(Math.floor((Date.now()-tic)/ 1000));
  if ( Math.floor((Date.now()-tic)/ 1000)>3){
      console.log('No more packets, Rx (bytes): ');
      console.log(totbytes.toString());
      var dur = Math.floor( ((Date.now()-start)/1000)-3 );
      console.log(totbytes.toString());
      console.log(dur.toString());
      console.log((totbytes/(dur*1e6)).toString());
      process.exit(1);
  }
}

server.bind(27001,'143.244.159.219');
setInterval(checkTime,1000);
/*setTimeout(function(){
server.close();
},8000);*/
