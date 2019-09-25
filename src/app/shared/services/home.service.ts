import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { QueryParam } from '../models/QueryBuilder';

@Injectable({
  providedIn: 'root'
})
export class HomeService {

  constructor(private http: HttpClient) { }

  getFilterValues() {
    return this.http.get('https://psnov1.lbl.gov:8082/generix/filters');
  }

  getUpdatedValues(filterQuery: QueryParam[]) {
   return this.http.post<any>('https://psnov1.lbl.gov:8082/generix/types_stat', filterQuery)
  }

}
