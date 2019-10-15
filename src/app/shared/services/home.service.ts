import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { QueryParam } from '../models/QueryBuilder';
import { environment } from 'src/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class HomeService {

  constructor(private http: HttpClient) { }

  getFilterValues() {
    return this.http.get(`${environment.baseURL}/filters`);
  }

  getUpdatedValues(filterQuery: QueryParam[]) {
   return this.http.post<any>(`${environment.baseURL}/types_stat`, filterQuery);
  }

}
