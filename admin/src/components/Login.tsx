import {useState} from "react";
import {session} from "../services/api";

export function Login(){
  const[email,setEmail]=useState("branch@demo.az"),[password,setPassword]=useState("Demo123!"),[error,setError]=useState("");
  return <div className="login"><form className="card" onSubmit={async event=>{
    event.preventDefault();
    try{await session.login(email,password);location.reload()}
    catch(value){setError(value instanceof Error?value.message:"Giriş alınmadı")}
  }}><div className="brand">MARTIQ</div><h1>İdarəetmə paneli</h1><p className="muted">Rolunuza uyğun təhlükəsiz idarəetmə sahəsi.</p><label className="field">E-poçt<input value={email} onChange={event=>setEmail(event.target.value)}/></label><label className="field">Şifrə<input type="password" value={password} onChange={event=>setPassword(event.target.value)}/></label>{error?<p className="error">{error}</p>:null}<button className="btn">Daxil ol</button></form></div>;
}
