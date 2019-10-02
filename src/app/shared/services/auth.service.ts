import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { map } from 'rxjs/operators';
import { JwtHelperService } from '@auth0/angular-jwt';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  constructor(
    private http: HttpClient,
    public jwtHelper: JwtHelperService
  ) { }


  isAuthenticated() {
    const token = localStorage.getItem('authToken');
    if (!token) {
      return false;
    } else {
      return !this.jwtHelper.isTokenExpired(token);
     }
  }

  submitLogin(username, password) {
    return this.http.post<any>('https://psnov1.lbl.gov:8082/generix/user_login', {username, password})
      .pipe(map(res => {
        const success = res.success;
        if (success) {
          localStorage.setItem('authToken', res.token);
        }
        return res;
      }));
  }

  logout() {
    localStorage.removeItem('authToken');
  }

}
