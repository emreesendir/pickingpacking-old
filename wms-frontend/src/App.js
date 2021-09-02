import { BrowserRouter, Route, Switch } from 'react-router-dom'
import Login from './global/Login'
import Mainmenu from './global/Mainmenu'
import Picking from './modules/picking/Picking'
import Packing from './modules/packing/Packing'
import Manage from './modules/manage/Manage'
import Dashboard from './modules/dashboard/Dashboard'

function App() {
  return (
    <BrowserRouter>
      <Switch>
        <Route exact path='/' component={Login} />
        <Route exact path='/login' component={Login} />
        <Route exact path='/menu' component={Mainmenu} />
        <Route path='/picking' component={Picking} />
        <Route path='/packing' component={Packing} />
        <Route path='/manage' component={Manage}/>
        <Route path='/dashboard' component={Dashboard}/>
        <Route path='*' component={() => <h1>PAGE NOT FOUND</h1>} />
      </Switch>
    </BrowserRouter>
  );
}

export default App;
