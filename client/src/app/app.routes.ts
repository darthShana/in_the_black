import { Routes } from '@angular/router';
import {SigninCallbackComponent} from "./auth/signin-callback.component";
import {HomeComponent} from "./home/home.component";


export const routes: Routes = [
  { path: '', component: HomeComponent },
  { path: 'signin-callback', component: SigninCallbackComponent },
];
