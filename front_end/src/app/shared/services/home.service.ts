import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { QueryParam } from '../models/QueryBuilder';
import { environment } from 'src/environments/environment';
import { Subject } from 'rxjs';
@Injectable({
  providedIn: 'root'
})
export class HomeService {

  constructor(private http: HttpClient) { }

  provenanceGraphSub: Subject<any> = new Subject();
  provenanceLoadingSub: Subject<any> = new Subject();

  getFilterValues() {
    return this.http.get(`${environment.baseURL}/filters`);
  }

  getUpdatedValues(filterQuery: QueryParam[]) {
   return this.http.post<any>(`${environment.baseURL}/types_stat`, filterQuery);
  }

  getReports() {
    return this.http.get(`${environment.baseURL}/reports`);
  }

  getReportItem(id: string) {
    return this.http.get(`${environment.baseURL}/reports/${id}`);
  }

  getProvenanceGraphData(filterQuery?: QueryParam[]) {
    this.provenanceLoadingSub.next(true); // tell component to display loading animation
    if (filterQuery) {
      this.http.post(`${environment.baseURL}/types_graph`, filterQuery)
        .subscribe(data => this.provenanceGraphSub.next(data));
    } else {
      this.http.get(`${environment.baseURL}/types_graph`)
        .subscribe(data => this.provenanceGraphSub.next(data));
    }
  }

  getProvenanceGraphSub() {
    return this.provenanceGraphSub.asObservable();
  }

  getProvenanceLoadingSub() {
    return this.provenanceLoadingSub.asObservable();
  }

}
