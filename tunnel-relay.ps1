$ErrorActionPreference='Stop'
$nic=Get-NetAdapter -Physical | Where-Object Status -eq 'Up' | Select-Object -First 1
$ip=(Get-NetIPAddress -InterfaceIndex $nic.ifIndex -AddressFamily IPv4 | Where-Object IPAddress -notlike '169.254*' | Select-Object -First 1).IPAddress
Add-Type -TypeDefinition @'
using System;using System.Net;using System.Net.Sockets;using System.Threading;using System.Threading.Tasks;
public static class PhysicalRelay {
 public static async Task Run(int index,string local){var listener=new TcpListener(IPAddress.Loopback,17845);listener.Start();Console.WriteLine("Physical interface relay ready "+index);int n=0;while(true){var c=await listener.AcceptTcpClientAsync();_ = Forward(c,index,local,(n++%2==0)?"198.41.192.67":"198.41.192.227");}}
 private static async Task Send(System.IO.Stream from,System.IO.Stream to){var buffer=new byte[512];bool first=true;int n;while((n=await from.ReadAsync(buffer,0,buffer.Length))>0){await to.WriteAsync(buffer,0,n);if(first){Console.WriteLine("Handshake bytes forwarded "+n);await Task.Delay(8);first=false;}}}
 private static async Task Forward(TcpClient client,int index,string local,string remote){var s=new Socket(AddressFamily.InterNetwork,SocketType.Stream,ProtocolType.Tcp);try{Console.WriteLine("Connecting edge "+remote);s.NoDelay=true;s.SetSocketOption(SocketOptionLevel.IP,(SocketOptionName)31,IPAddress.HostToNetworkOrder(index));s.Bind(new IPEndPoint(IPAddress.Parse(local),0));using(var timeout=new CancellationTokenSource(5000)){await s.ConnectAsync(new IPEndPoint(IPAddress.Parse(remote),7844),timeout.Token);}Console.WriteLine("Edge connected "+remote);using(var upstream=new NetworkStream(s,true)){var downstream=client.GetStream();await Task.WhenAny(Send(downstream,upstream),upstream.CopyToAsync(downstream));}}catch(Exception e){Console.Error.WriteLine(e.Message);}finally{client.Dispose();s.Dispose();}}
}
'@
[PhysicalRelay]::Run($nic.ifIndex,$ip).GetAwaiter().GetResult()


