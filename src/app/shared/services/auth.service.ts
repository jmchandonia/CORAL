import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class AuthService {

  constructor(
    private http: HttpClient
  ) { }

  private test = false;

  isAuthenticated() {
    return this.test;
  }

  changeTest() {
    this.test = !this.test;
  }

}
