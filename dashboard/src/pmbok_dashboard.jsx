import { useState, useEffect, useCallback } from "react";
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

const API_BASE = "http://localhost:8000";
const POLL_MS  = 30_000;

// ── Theme definitions ─────────────────────────────────────────────────────────
const THEMES = {
  light: {
    bg:"#F7F6F3", surface:"#FFFFFF", panel:"#F2F1EE", border:"#E2E0DB", borderDk:"#C8C5BC",
    text:"#1A1916", textSub:"#5C5A54", textDim:"#9E9B94", ink:"#0F0E0C",
    navBg:"#FFFFFF", navBorder:"#E2E0DB",
    red:"#B91C1C", redBg:"#FEF2F2", redBdr:"#FECACA",
    amber:"#92400E", amberBg:"#FFFBEB", amberBdr:"#FDE68A",
    green:"#14532D", greenBg:"#F0FDF4", greenBdr:"#BBF7D0",
    blue:"#1E3A8A", blueBg:"#EFF6FF", blueBdr:"#BFDBFE",
    purple:"#581C87", purpleBg:"#FAF5FF", purpleBdr:"#E9D5FF",
    chartGrid:"#E2E0DB", tooltipShadow:"rgba(0,0,0,0.08)",
  },
  dark: {
    bg:"#0D0F14", surface:"#141720", panel:"#1A1E28", border:"#252A38", borderDk:"#323848",
    text:"#E8ECF4", textSub:"#9BA3BF", textDim:"#525A78", ink:"#FFFFFF",
    navBg:"#0D0F14", navBorder:"#1E2330",
    red:"#F87171", redBg:"rgba(248,113,113,0.1)", redBdr:"rgba(248,113,113,0.25)",
    amber:"#FCD34D", amberBg:"rgba(252,211,77,0.1)", amberBdr:"rgba(252,211,77,0.25)",
    green:"#4ADE80", greenBg:"rgba(74,222,128,0.1)", greenBdr:"rgba(74,222,128,0.25)",
    blue:"#60A5FA", blueBg:"rgba(96,165,250,0.1)", blueBdr:"rgba(96,165,250,0.25)",
    purple:"#C084FC", purpleBg:"rgba(192,132,252,0.1)", purpleBdr:"rgba(192,132,252,0.25)",
    chartGrid:"#252A38", tooltipShadow:"rgba(0,0,0,0.4)",
  }
};

const PROB_DOT = { Low:"#22C55E", Medium:"#F59E0B", High:"#EF4444", Critical:"#E11D48" };
const fmtDate = d => d ? new Date(d).toLocaleDateString("en-GB",{day:"2-digit",month:"short",year:"numeric"}) : "—";
const fmtTime = d => d ? new Date(d).toLocaleTimeString("en-GB",{hour:"2-digit",minute:"2-digit"}) : "—";
const pcnt    = (a,b) => b===0 ? 0 : Math.round(a/b*100);

// ── Pill ──────────────────────────────────────────────────────────────────────
const Pill = ({label,bg,text,border}) => (
  <span style={{display:"inline-flex",alignItems:"center",padding:"2px 8px",borderRadius:4,
    fontSize:11,fontWeight:600,letterSpacing:"0.04em",background:bg,color:text,
    border:`1px solid ${border}`,whiteSpace:"nowrap"}}>{label}</span>
);

// ── StatusDot ─────────────────────────────────────────────────────────────────
const StatusDot = ({color,pulse}) => (
  <span style={{position:"relative",display:"inline-flex",alignItems:"center",justifyContent:"center",flexShrink:0}}>
    {pulse && <span style={{position:"absolute",width:10,height:10,borderRadius:"50%",
      background:color,opacity:0.3,animation:"ripple 1.8s ease-out infinite"}}/>}
    <span style={{width:6,height:6,borderRadius:"50%",background:color,display:"block"}}/>
  </span>
);

// ── ImpactBar ─────────────────────────────────────────────────────────────────
const ImpactBar = ({score,T}) => {
  const c = score>=8?T.red:score>=5?T.amber:T.green;
  return (
    <div style={{display:"flex",alignItems:"center",gap:8}}>
      <div style={{flex:1,height:3,background:T.border,borderRadius:2}}>
        <div style={{width:`${score*10}%`,height:"100%",background:c,borderRadius:2,transition:"width 0.5s"}}/>
      </div>
      <span style={{fontSize:11,fontWeight:700,color:c,width:14,textAlign:"right"}}>{score}</span>
    </div>
  );
};

// ── VelocityBar ───────────────────────────────────────────────────────────────
const VelocityBar = ({value,T}) => {
  const c = value>=85?T.green:value>=60?T.amber:T.red;
  return (
    <div style={{display:"flex",alignItems:"center",gap:8}}>
      <div style={{flex:1,height:4,background:T.border,borderRadius:2}}>
        <div style={{width:`${value}%`,height:"100%",background:c,borderRadius:2,transition:"width 0.8s"}}/>
      </div>
      <span style={{fontSize:11,fontWeight:700,color:c,width:30,textAlign:"right"}}>{value}%</span>
    </div>
  );
};

// ── Chart tooltip ─────────────────────────────────────────────────────────────
const ChartTip = ({active,payload,label,T}) => {
  if(!active||!payload?.length) return null;
  return (
    <div style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:6,
      padding:"10px 14px",boxShadow:`0 4px 16px ${T.tooltipShadow}`}}>
      <div style={{fontSize:11,color:T.textDim,marginBottom:6,fontWeight:600}}>{label}</div>
      {payload.map(p=>(
        <div key={p.name} style={{display:"flex",alignItems:"center",gap:8,fontSize:12}}>
          <span style={{width:8,height:8,borderRadius:2,background:p.color,display:"block",flexShrink:0}}/>
          <span style={{color:T.textSub}}>{p.name}</span>
          <span style={{fontWeight:700,color:T.text,marginLeft:"auto",paddingLeft:12}}>{p.value}</span>
        </div>
      ))}
    </div>
  );
};

// ── KPI card ──────────────────────────────────────────────────────────────────
const KPICard = ({label,value,sub,accent,icon,T}) => (
  <div style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:8,
    padding:"16px 18px",display:"flex",flexDirection:"column",gap:6}}>
    <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start"}}>
      <span style={{fontSize:10,color:T.textDim,fontWeight:700,letterSpacing:"0.08em",textTransform:"uppercase"}}>{label}</span>
      {icon&&<span style={{fontSize:13,opacity:0.35}}>{icon}</span>}
    </div>
    <span style={{fontSize:26,fontWeight:800,color:accent||T.text,lineHeight:1,fontVariantNumeric:"tabular-nums"}}>{value??"—"}</span>
    {sub&&<span style={{fontSize:11,color:T.textDim}}>{sub}</span>}
  </div>
);

// ── Section label ─────────────────────────────────────────────────────────────
const SectionLabel = ({label,T}) => (
  <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:14}}>
    <span style={{fontSize:10,fontWeight:700,letterSpacing:"0.1em",textTransform:"uppercase",color:T.textDim,whiteSpace:"nowrap"}}>{label}</span>
    <div style={{flex:1,height:1,background:T.border}}/>
  </div>
);

// ── Risk row ──────────────────────────────────────────────────────────────────
const RiskRow = ({risk,expanded,onToggle,T}) => {
  const statusColors = {Open:T.red,Mitigating:T.amber,Resolved:T.green,Accepted:T.textDim};
  const catColors    = {Technical:T.blue,Schedule:T.amber,Resource:T.purple,Quality:T.green,External:"#EC4899"};
  return (
    <div style={{background:T.surface,border:`1px solid ${expanded?T.borderDk:T.border}`,
      borderRadius:8,overflow:"hidden",transition:"border-color 0.15s"}}>
      <div onClick={onToggle} style={{padding:"14px 16px",cursor:"pointer",
        display:"flex",alignItems:"center",gap:12}}>
        <StatusDot color={PROB_DOT[risk.probability]||T.textDim}/>
        <div style={{flex:1,minWidth:0}}>
          <div style={{fontSize:13,fontWeight:600,color:T.text,marginBottom:5,lineHeight:1.35}}>{risk.title}</div>
          <div style={{display:"flex",gap:5,flexWrap:"wrap"}}>
            <Pill label={risk.risk_id} bg={T.panel} text={T.textSub} border={T.border}/>
            <Pill label={risk.category} bg={T.blueBg} text={catColors[risk.category]||T.blue} border={T.blueBdr}/>
            <Pill label={risk.probability} bg={T.redBg} text={T.red} border={T.redBdr}/>
          </div>
        </div>
        <div style={{display:"flex",flexDirection:"column",alignItems:"flex-end",gap:6,flexShrink:0,minWidth:140}}>
          <Pill label={risk.status} bg={T.panel} text={statusColors[risk.status]||T.textSub} border={T.border}/>
          <div style={{width:"100%"}}><ImpactBar score={risk.impact_score} T={T}/></div>
        </div>
        <span style={{color:T.textDim,fontSize:11,marginLeft:2,flexShrink:0}}>{expanded?"▲":"▼"}</span>
      </div>
      {expanded&&(
        <div style={{padding:"0 16px 16px",borderTop:`1px solid ${T.border}`}}>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16,marginTop:16}}>
            <div>
              <div style={{fontSize:10,fontWeight:700,letterSpacing:"0.08em",textTransform:"uppercase",color:T.textDim,marginBottom:5}}>Mitigation</div>
              <p style={{fontSize:12,color:T.textSub,lineHeight:1.7,margin:0}}>{risk.mitigation}</p>
            </div>
            {risk.contingency&&(
              <div>
                <div style={{fontSize:10,fontWeight:700,letterSpacing:"0.08em",textTransform:"uppercase",color:T.textDim,marginBottom:5}}>Contingency</div>
                <p style={{fontSize:12,color:T.textSub,lineHeight:1.7,margin:0}}>{risk.contingency}</p>
              </div>
            )}
          </div>
          <div style={{display:"flex",gap:20,marginTop:14,flexWrap:"wrap"}}>
            {[["Owner",risk.owner],["Source",risk.raised_from],["Identified",fmtDate(risk.date)],["Risk Score",risk.risk_score]].map(([l,v])=>(
              <div key={l}>
                <div style={{fontSize:10,fontWeight:700,letterSpacing:"0.08em",textTransform:"uppercase",color:T.textDim,marginBottom:3}}>{l}</div>
                <div style={{fontSize:12,color:l==="Risk Score"?T.red:T.text,fontWeight:l==="Risk Score"?700:500}}>{v}</div>
              </div>
            ))}
          </div>
          {risk.tags?.length>0&&(
            <div style={{display:"flex",gap:4,marginTop:10,flexWrap:"wrap"}}>
              {risk.tags.map(t=><Pill key={t} label={t} bg={T.panel} text={T.textDim} border={T.border}/>)}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ── Sprint card ───────────────────────────────────────────────────────────────
const SprintCard = ({sprint,T}) => {
  const v = sprint.velocity_pct ?? pcnt(sprint.metrics?.story_points_completed, sprint.metrics?.story_points_planned);
  const isActive = sprint.status==="Active";
  const statusC  = {Complete:T.green,Active:T.blue,Cancelled:T.textDim};
  return (
    <div style={{background:T.surface,border:`1px solid ${isActive?T.borderDk:T.border}`,
      borderRadius:8,padding:18,borderLeft:isActive?`3px solid ${T.blue}`:`3px solid transparent`}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:14}}>
        <div>
          <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:3}}>
            <span style={{fontSize:15,fontWeight:800,color:T.text}}>{sprint.sprint_id}</span>
            <Pill label={sprint.status} bg={T.panel} text={statusC[sprint.status]||T.textDim} border={T.border}/>
          </div>
          <span style={{fontSize:11,color:T.textDim}}>{fmtDate(sprint.start_date)} — {fmtDate(sprint.end_date)}</span>
        </div>
        <div style={{textAlign:"right"}}>
          <div style={{fontSize:10,color:T.textDim,marginBottom:2}}>AI Confidence</div>
          <div style={{fontSize:16,fontWeight:800,color:(sprint.ai_confidence||0)>=0.85?T.green:T.amber}}>
            {Math.round((sprint.ai_confidence||0)*100)}%
          </div>
        </div>
      </div>
      <div style={{marginBottom:14}}>
        <div style={{display:"flex",justifyContent:"space-between",marginBottom:5}}>
          <span style={{fontSize:11,color:T.textDim,fontWeight:600}}>Velocity</span>
          <span style={{fontSize:11,color:T.textSub}}>{sprint.metrics?.story_points_completed} / {sprint.metrics?.story_points_planned} pts</span>
        </div>
        <VelocityBar value={v} T={T}/>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:8,marginBottom:12}}>
        {[["Commits",sprint.metrics?.commits_total],["PRs merged",sprint.metrics?.prs_merged],["Issues ✓",sprint.metrics?.issues_closed]].map(([l,v])=>(
          <div key={l} style={{textAlign:"center",padding:"9px 4px",background:T.panel,borderRadius:6,border:`1px solid ${T.border}`}}>
            <div style={{fontSize:17,fontWeight:800,color:T.text,fontVariantNumeric:"tabular-nums"}}>{v}</div>
            <div style={{fontSize:10,color:T.textDim,marginTop:2}}>{l}</div>
          </div>
        ))}
      </div>
      {sprint.blockers?.length>0&&(
        <div style={{marginBottom:10}}>
          {sprint.blockers.map((b,i)=>(
            <div key={i} style={{display:"flex",gap:8,padding:"7px 10px",background:T.redBg,
              border:`1px solid ${T.redBdr}`,borderRadius:6,marginBottom:5}}>
              <span style={{fontSize:10,fontWeight:700,color:T.red,flexShrink:0,marginTop:1}}>BLOCKER</span>
              <span style={{fontSize:12,color:T.textSub,lineHeight:1.5}}>{b.description}</span>
            </div>
          ))}
        </div>
      )}
      {sprint.achievements?.length>0&&(
        <div style={{marginBottom:10}}>
          {sprint.achievements.map((a,i)=>(
            <div key={i} style={{display:"flex",gap:8,padding:"5px 0",
              borderBottom:i<sprint.achievements.length-1?`1px solid ${T.border}`:"none"}}>
              <span style={{color:T.green,fontSize:12,flexShrink:0}}>✓</span>
              <span style={{fontSize:12,color:T.textSub}}>{a}</span>
            </div>
          ))}
        </div>
      )}
      <p style={{fontSize:12,color:T.textSub,lineHeight:1.7,margin:0,paddingTop:8,borderTop:`1px solid ${T.border}`}}>{sprint.summary}</p>
    </div>
  );
};

// ── Run row ───────────────────────────────────────────────────────────────────
const RunRow = ({run,T}) => {
  const typeBg   = {RISK:T.redBg,VELOCITY:T.blueBg,STAKEHOLDER:T.purpleBg,NO_ACTION:T.panel,UNKNOWN:T.amberBg};
  const typeText = {RISK:T.red,VELOCITY:T.blue,STAKEHOLDER:T.purple,NO_ACTION:T.textDim,UNKNOWN:T.amber};
  return (
    <div style={{display:"flex",alignItems:"center",gap:10,padding:"9px 12px",
      background:T.surface,border:`1px solid ${T.border}`,borderRadius:6}}>
      <StatusDot color={run.success?"#22C55E":T.red}/>
      <span style={{fontSize:10,color:T.textDim,width:44,flexShrink:0}}>{fmtTime(run.timestamp)}</span>
      <Pill label={run.output_type} bg={typeBg[run.output_type]||T.panel} text={typeText[run.output_type]||T.textDim} border={T.border}/>
      <span style={{flex:1,fontSize:11,color:T.textDim,fontFamily:"monospace",overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{run.run_id}</span>
      <span style={{fontSize:10,color:T.textDim,flexShrink:0,fontVariantNumeric:"tabular-nums"}}>
        {((run.input_tokens||0)+(run.output_tokens||0)).toLocaleString()} tok
      </span>
      <span style={{fontSize:10,color:T.textDim,width:34,textAlign:"right",flexShrink:0}}>{run.duration_sec?.toFixed(1)}s</span>
    </div>
  );
};

// ── Trigger form ──────────────────────────────────────────────────────────────
const TriggerForm = ({onTriggered,T}) => {
  const [repo,setRepo]       = useState("");
  const [dryRun,setDryRun]   = useState(true);
  const [loading,setLoading] = useState(false);
  const [msg,setMsg]         = useState(null);

  const trigger = async () => {
    if(!repo.trim()){
      setMsg({ok:false,text:"Please enter a repository in owner/repo format."});
      return;
    }
    setLoading(true); setMsg(null);
    try {
      const r = await fetch(`${API_BASE}/api/pipeline/trigger`,{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({repo:repo.trim(),dry_run:dryRun}),
      });
      const data = await r.json();
      if(r.ok){
        setMsg({ok:true,text:`Pipeline triggered for ${repo}. Check audit log in ~5 seconds.`});
        setTimeout(onTriggered,5000);
      } else {
        // Show the actual API error clearly
        setMsg({ok:false,text:data.detail||`Error ${r.status}: Could not trigger pipeline.`});
      }
    } catch(e){
      setMsg({ok:false,text:`Cannot reach API server at ${API_BASE}. Is uvicorn running?`});
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:8,padding:20}}>
      <div style={{fontSize:11,fontWeight:700,color:T.textDim,marginBottom:12,
        letterSpacing:"0.08em",textTransform:"uppercase"}}>Manual Run</div>
      <div style={{display:"flex",gap:8,flexWrap:"wrap",alignItems:"center"}}>
        <input value={repo} onChange={e=>setRepo(e.target.value)}
          onKeyDown={e=>e.key==="Enter"&&trigger()}
          placeholder="owner/repository-name"
          style={{flex:1,minWidth:200,padding:"8px 12px",borderRadius:6,
            background:T.panel,border:`1px solid ${T.border}`,color:T.text,
            fontSize:13,fontFamily:"monospace",outline:"none"}}/>
        <label style={{display:"flex",alignItems:"center",gap:6,fontSize:12,
          color:T.textSub,cursor:"pointer",userSelect:"none",flexShrink:0}}>
          <input type="checkbox" checked={dryRun} onChange={e=>setDryRun(e.target.checked)}
            style={{accentColor:T.blue,cursor:"pointer"}}/>
          Dry run
        </label>
        <button onClick={trigger} disabled={loading}
          style={{padding:"8px 20px",borderRadius:6,border:"none",
            cursor:loading?"not-allowed":"pointer",
            background:loading?T.border:T.blue,
            color:loading?T.textDim:"#fff",
            fontSize:12,fontWeight:700,transition:"all 0.15s",
            flexShrink:0,minWidth:100}}>
          {loading?"Running…":"Run Agent"}
        </button>
      </div>
      {msg&&(
        <div style={{marginTop:10,padding:"9px 12px",borderRadius:6,fontSize:12,lineHeight:1.5,
          background:msg.ok?T.greenBg:T.redBg,
          border:`1px solid ${msg.ok?T.greenBdr:T.redBdr}`,
          color:msg.ok?T.green:T.red}}>
          {msg.text}
          {!msg.ok&&msg.text.includes("GITHUB_TOKEN")&&(
            <div style={{marginTop:6,fontSize:11,opacity:0.8}}>
              Add GITHUB_TOKEN to your .env file and restart the API server.
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// ── Theme toggle button ───────────────────────────────────────────────────────
const ThemeToggle = ({isDark,onToggle,T}) => (
  <button onClick={onToggle}
    style={{padding:"5px 12px",borderRadius:6,border:`1px solid ${T.border}`,
      background:T.panel,color:T.textSub,fontSize:12,cursor:"pointer",
      display:"flex",alignItems:"center",gap:6,fontFamily:"inherit",flexShrink:0}}>
    {isDark?"☀ Light":"◑ Dark"}
  </button>
);

// ── Main ──────────────────────────────────────────────────────────────────────
export default function ProjectDashboard(){
  const [isDark,setIsDark]         = useState(false);
  const T                          = isDark ? THEMES.dark : THEMES.light;

  const [data,setData]             = useState(null);
  const [loading,setLoading]       = useState(true);
  const [apiError,setApiError]     = useState(false);
  const [lastFetched,setLF]        = useState(null);
  const [expandedRisk,setExpRisk]  = useState(null);
  const [activeTab,setActiveTab]   = useState("risks");
  const [filter,setFilter]         = useState("All");

  const fetchData = useCallback(async()=>{
    try{
      const r = await fetch(`${API_BASE}/api/dashboard`);
      if(!r.ok) throw new Error();
      setData(await r.json()); setApiError(false); setLF(new Date());
    }catch{ setApiError(true); }
    finally{ setLoading(false); }
  },[]);

  useEffect(()=>{
    fetchData();
    const id = setInterval(fetchData,POLL_MS);
    return ()=>clearInterval(id);
  },[fetchData]);

  const risks   = data?.risks||[];
  const sprints = data?.sprints||[];
  const runs    = data?.pipeline_runs||[];
  const kpis    = data?.kpis||{};
  const meta    = data?.meta||{};

  const filtered  = filter==="All"?risks:risks.filter(r=>r.category===filter||r.status===filter||r.probability===filter);
  const velData   = sprints.map(s=>({sprint:s.sprint_id,Planned:s.metrics?.story_points_planned||0,Done:s.metrics?.story_points_completed||0,pct:s.velocity_pct||0}));
  const commitData= sprints.map(s=>({sprint:s.sprint_id,Commits:s.metrics?.commits_total||0}));
  const typeCount = runs.reduce((a,r)=>({...a,[r.output_type]:(a[r.output_type]||0)+1}),{});
  const totalTok  = runs.reduce((s,r)=>s+(r.input_tokens||0)+(r.output_tokens||0),0);
  const successPct= runs.length?Math.round(runs.filter(r=>r.success).length/runs.length*100):0;

  const tabs=[
    {id:"risks",   label:"Risks",   count:risks.length},
    {id:"velocity",label:"Velocity",count:sprints.length},
    {id:"pipeline",label:"Pipeline",count:runs.length},
  ];

  const kpiCards = loading ? [] : [
    {label:"Open Risks",     value:kpis.open_risks,      sub:`${kpis.critical_risks||0} critical`,  accent:kpis.open_risks>0?T.red:T.green,    icon:"⚠"},
    {label:"Sprint Velocity",value:`${kpis.sprint_velocity||0}%`,sub:kpis.current_sprint,           accent:kpis.sprint_velocity>=85?T.green:kpis.sprint_velocity>=60?T.amber:T.red,icon:"◈"},
    {label:"Active Blockers",value:kpis.active_blockers,  sub:"this sprint",                        accent:kpis.active_blockers>0?T.red:T.green,icon:"■"},
    {label:"Agent Runs",     value:kpis.pipeline_runs,    sub:`${successPct}% success`,             accent:T.blue,  icon:"↻"},
    {label:"Tokens Used",    value:`${((kpis.total_tokens||totalTok)/1000).toFixed(1)}k`,sub:"session",accent:T.purple,icon:"◇"},
    {label:"AI Confidence",  value:`${Math.round((kpis.ai_confidence||0)*100)}%`,sub:"current sprint",accent:(kpis.ai_confidence||0)>=0.85?T.green:T.amber,icon:"◎"},
  ];

  return(
    <div style={{minHeight:"100vh",background:T.bg,color:T.text,fontFamily:"system-ui,'Segoe UI',sans-serif"}}>
      <style>{`
        *{box-sizing:border-box;margin:0;padding:0}
        ::-webkit-scrollbar{width:5px}
        ::-webkit-scrollbar-track{background:${T.bg}}
        ::-webkit-scrollbar-thumb{background:${T.border};border-radius:3px}
        input:focus{border-color:${T.blue}!important;outline:none!important}
        @keyframes ripple{0%{transform:scale(1);opacity:0.4}100%{transform:scale(2.6);opacity:0}}
        @keyframes fadeIn{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:translateY(0)}}
      `}</style>

      {/* ── Top nav ── */}
      <div style={{background:T.navBg,borderBottom:`1px solid ${T.navBorder}`,
        padding:"0 24px",position:"sticky",top:0,zIndex:100}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",height:50,maxWidth:"100%"}}>
          <div style={{display:"flex",alignItems:"center",gap:16}}>
            <span style={{fontSize:15,fontWeight:800,color:T.ink,letterSpacing:"-0.02em",whiteSpace:"nowrap"}}>
              Project Dashboard
            </span>
            <div style={{width:1,height:14,background:T.border}}/>
            <span style={{fontSize:12,color:T.textDim}}>PROJ-001</span>
            <div style={{width:1,height:14,background:T.border}}/>
            <span style={{fontSize:11,color:T.textDim}}>
              Sprint <span style={{fontWeight:700,color:T.text}}>{kpis.current_sprint||"—"}</span>
            </span>
          </div>
          <div style={{display:"flex",alignItems:"center",gap:10}}>
            <div style={{display:"flex",alignItems:"center",gap:6}}>
              <StatusDot color={apiError?T.amber:"#22C55E"} pulse={!apiError}/>
              <span style={{fontSize:11,color:T.textDim}}>
                {apiError?"Offline":lastFetched?`Updated ${fmtTime(lastFetched)}`:"Connecting…"}
              </span>
            </div>
            <ThemeToggle isDark={isDark} onToggle={()=>setIsDark(d=>!d)} T={T}/>
            <button onClick={fetchData}
              style={{padding:"5px 12px",borderRadius:6,border:`1px solid ${T.border}`,
                background:"transparent",color:T.textSub,fontSize:11,cursor:"pointer",fontFamily:"inherit"}}>
              ↻ Refresh
            </button>
          </div>
        </div>
      </div>

      {/* ── Content ── */}
      <div style={{padding:"24px",maxWidth:"100%"}}>

        {/* API offline banner */}
        {apiError&&(
          <div style={{padding:"10px 16px",borderRadius:8,background:T.amberBg,
            border:`1px solid ${T.amberBdr}`,marginBottom:20,
            display:"flex",justifyContent:"space-between",alignItems:"center",gap:12,flexWrap:"wrap"}}>
            <span style={{fontSize:12,color:T.amber}}>
              API offline — <code style={{fontFamily:"monospace",fontSize:11}}>uvicorn api.main:app --port 8000</code>
            </span>
            {lastFetched&&<span style={{fontSize:11,color:T.textDim}}>Last live: {fmtTime(lastFetched)}</span>}
          </div>
        )}

        {/* KPI strip */}
        <div style={{display:"grid",gridTemplateColumns:"repeat(6,1fr)",gap:10,marginBottom:24}}>
          {loading?Array(6).fill(0).map((_,i)=>(
            <div key={i} style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:8,padding:"16px 18px",height:84}}>
              <div style={{height:8,width:"55%",background:T.border,borderRadius:3,marginBottom:10}}/>
              <div style={{height:22,width:"40%",background:T.border,borderRadius:3}}/>
            </div>
          )):kpiCards.map(s=><KPICard key={s.label} {...s} T={T}/>)}
        </div>

        {/* Tabs */}
        <div style={{display:"flex",gap:0,marginBottom:20,borderBottom:`1px solid ${T.border}`}}>
          {tabs.map(t=>(
            <button key={t.id} onClick={()=>setActiveTab(t.id)}
              style={{padding:"8px 18px",border:"none",cursor:"pointer",background:"transparent",
                color:activeTab===t.id?T.ink:T.textDim,
                fontSize:13,fontWeight:activeTab===t.id?700:500,
                borderBottom:`2px solid ${activeTab===t.id?T.ink:"transparent"}`,
                marginBottom:-1,display:"flex",alignItems:"center",gap:7,
                transition:"all 0.15s",fontFamily:"inherit"}}>
              {t.label}
              <span style={{background:activeTab===t.id?T.ink:T.border,
                color:activeTab===t.id?"#fff":T.textDim,
                borderRadius:10,padding:"1px 7px",fontSize:10,fontWeight:700}}>{t.count}</span>
            </button>
          ))}
        </div>

        {/* ── Risks tab ── */}
        {activeTab==="risks"&&(
          <div style={{animation:"fadeIn 0.2s ease"}}>
            <div style={{display:"flex",gap:5,marginBottom:16,flexWrap:"wrap"}}>
              {["All","Open","Mitigating","Technical","Resource","High","Critical"].map(f=>(
                <button key={f} onClick={()=>setFilter(f)}
                  style={{padding:"4px 12px",borderRadius:20,cursor:"pointer",fontFamily:"inherit",
                    border:`1px solid ${filter===f?T.ink:T.border}`,
                    background:filter===f?T.ink:"transparent",
                    color:filter===f?"#fff":T.textSub,
                    fontSize:12,fontWeight:500,transition:"all 0.15s"}}>{f}</button>
              ))}
            </div>
            {loading?Array(3).fill(0).map((_,i)=>(
              <div key={i} style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:8,padding:16,marginBottom:8,height:80}}>
                <div style={{height:12,width:"60%",background:T.border,borderRadius:3,marginBottom:8}}/>
                <div style={{height:8,width:"35%",background:T.border,borderRadius:3}}/>
              </div>
            )):(
              <div style={{display:"flex",flexDirection:"column",gap:7}}>
                {filtered.map(r=>(
                  <RiskRow key={r.risk_id} risk={r} T={T}
                    expanded={expandedRisk===r.risk_id}
                    onToggle={()=>setExpRisk(expandedRisk===r.risk_id?null:r.risk_id)}/>
                ))}
                {filtered.length===0&&(
                  <div style={{padding:36,textAlign:"center",color:T.textDim,fontSize:13,
                    background:T.surface,borderRadius:8,border:`1px solid ${T.border}`}}>
                    No risks match this filter.
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ── Velocity tab ── */}
        {activeTab==="velocity"&&(
          <div style={{animation:"fadeIn 0.2s ease",display:"flex",flexDirection:"column",gap:24}}>
            <div>
              <SectionLabel label="Story Points by Sprint" T={T}/>
              <div style={{height:200,background:T.surface,border:`1px solid ${T.border}`,borderRadius:8,padding:"14px 8px 8px"}}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={velData} barGap={6}>
                    <XAxis dataKey="sprint" tick={{fill:T.textDim,fontSize:11}} axisLine={{stroke:T.border}} tickLine={false}/>
                    <YAxis tick={{fill:T.textDim,fontSize:11}} axisLine={false} tickLine={false} width={28}/>
                    <Tooltip content={props=><ChartTip {...props} T={T}/>} cursor={{fill:T.panel}}/>
                    <Bar dataKey="Planned" fill={T.border} radius={[3,3,0,0]}/>
                    <Bar dataKey="Done" radius={[3,3,0,0]}>
                      {velData.map((d,i)=><Cell key={i} fill={d.pct>=85?"#22C55E":d.pct>=60?"#F59E0B":"#EF4444"}/>)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div>
              <SectionLabel label="Commit Activity" T={T}/>
              <div style={{height:150,background:T.surface,border:`1px solid ${T.border}`,borderRadius:8,padding:"14px 8px 8px"}}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={commitData}>
                    <defs>
                      <linearGradient id="cg" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%"  stopColor={T.blue} stopOpacity={isDark?0.3:0.15}/>
                        <stop offset="95%" stopColor={T.blue} stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <XAxis dataKey="sprint" tick={{fill:T.textDim,fontSize:11}} axisLine={{stroke:T.border}} tickLine={false}/>
                    <YAxis tick={{fill:T.textDim,fontSize:11}} axisLine={false} tickLine={false} width={28}/>
                    <Tooltip content={props=><ChartTip {...props} T={T}/>}/>
                    <Area type="monotone" dataKey="Commits" stroke={T.blue} strokeWidth={2} fill="url(#cg)" dot={{fill:T.blue,r:4,strokeWidth:0}}/>
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div>
              <SectionLabel label="Sprint Detail" T={T}/>
              <div style={{display:"flex",flexDirection:"column",gap:10}}>
                {[...sprints].reverse().map(s=><SprintCard key={s.sprint_id} sprint={s} T={T}/>)}
              </div>
            </div>
          </div>
        )}

        {/* ── Pipeline tab ── */}
        {activeTab==="pipeline"&&(
          <div style={{animation:"fadeIn 0.2s ease",display:"flex",flexDirection:"column",gap:20}}>
            <TriggerForm onTriggered={fetchData} T={T}/>
            <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:10}}>
              {[
                {label:"Total Runs",  value:runs.length,                           accent:T.blue},
                {label:"Successful",  value:runs.filter(r=>r.success).length,      accent:T.green},
                {label:"Failed",      value:runs.filter(r=>!r.success).length,     accent:T.red},
                {label:"Avg Duration",value:runs.length?`${(runs.reduce((s,r)=>s+(r.duration_sec||0),0)/runs.length).toFixed(1)}s`:"—",accent:T.purple},
              ].map(s=><KPICard key={s.label} {...s} T={T}/>)}
            </div>

            <div>
              <SectionLabel label="Audit Log" T={T}/>
              <div style={{display:"flex",flexDirection:"column",gap:5}}>
                {runs.length===0
                  ?<div style={{padding:28,textAlign:"center",color:T.textDim,fontSize:13,background:T.surface,border:`1px solid ${T.border}`,borderRadius:8}}>No runs recorded yet.</div>
                  :runs.map(r=><RunRow key={r.run_id+r.timestamp} run={r} T={T}/>)
                }
              </div>
            </div>

            {Object.keys(typeCount).length>0&&(
              <div>
                <SectionLabel label="Output Distribution" T={T}/>
                <div style={{display:"flex",gap:8,flexWrap:"wrap"}}>
                  {Object.entries(typeCount).map(([type,count])=>{
                    const typeBg  ={RISK:T.redBg,VELOCITY:T.blueBg,STAKEHOLDER:T.purpleBg,NO_ACTION:T.panel,UNKNOWN:T.amberBg};
                    const typeText={RISK:T.red,VELOCITY:T.blue,STAKEHOLDER:T.purple,NO_ACTION:T.textDim,UNKNOWN:T.amber};
                    return(
                      <div key={type} style={{flex:1,minWidth:90,padding:"14px 16px",
                        background:typeBg[type]||T.panel,border:`1px solid ${T.border}`,
                        borderRadius:8,textAlign:"center"}}>
                        <div style={{fontSize:22,fontWeight:800,color:typeText[type]||T.textSub,fontVariantNumeric:"tabular-nums"}}>{count}</div>
                        <div style={{fontSize:10,color:T.textDim,marginTop:4,letterSpacing:"0.06em"}}>{type}</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <div>
              <SectionLabel label="Token Budget" T={T}/>
              <div style={{background:T.surface,border:`1px solid ${T.border}`,borderRadius:8,padding:16}}>
                <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}>
                  <span style={{fontSize:12,color:T.textSub}}>Session usage</span>
                  <span style={{fontSize:12,color:T.text,fontVariantNumeric:"tabular-nums"}}>
                    {totalTok.toLocaleString()} <span style={{color:T.textDim}}>/ 50,000</span>
                  </span>
                </div>
                <div style={{height:5,background:T.border,borderRadius:3}}>
                  <div style={{width:`${Math.min(pcnt(totalTok,50000),100)}%`,height:"100%",
                    background:T.blue,borderRadius:3,transition:"width 0.8s"}}/>
                </div>
                <span style={{fontSize:11,color:T.textDim,marginTop:5,display:"block"}}>{pcnt(totalTok,50000)}% consumed</span>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div style={{marginTop:40,paddingTop:16,borderTop:`1px solid ${T.border}`,
          display:"flex",justifyContent:"space-between",flexWrap:"wrap",gap:8}}>
          <span style={{fontSize:11,color:T.textDim}}>Agentic PMBOK Toolkit · AI Scrum Master</span>
          <span style={{fontSize:11,color:T.textDim}}>API: {API_BASE} · Auto-refresh every 30s</span>
        </div>
      </div>
    </div>
  );
}
