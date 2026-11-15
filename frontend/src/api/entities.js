import {api} from './client.js';
export const datasets={list:()=>api('/datasets'),get:id=>api('/datasets/'+id),create:data=>api('/datasets',{method:'POST',body:JSON.stringify(data)})};
export const jobs={list:()=>api('/jobs'),get:id=>api('/jobs/'+id),create:data=>api('/jobs',{method:'POST',body:JSON.stringify(data)}),approve:id=>api('/jobs/'+id+'/approve',{method:'POST'})};
export const reports={list:()=>api('/reports'),create:data=>api('/reports',{method:'POST',body:JSON.stringify(data)}),toggle:id=>api('/reports/'+id+'/toggle',{method:'POST'}),deliveries:()=>api('/deliveries')};
export const products={list:()=>api('/products'),create:data=>api('/products',{method:'POST',body:JSON.stringify(data)}),versions:id=>api('/products/'+id+'/versions'),publish:(id,data)=>api('/products/'+id+'/publish',{method:'POST',body:JSON.stringify(data)}),rollback:(id,data)=>api('/products/'+id+'/rollback',{method:'POST',body:JSON.stringify(data)})};
