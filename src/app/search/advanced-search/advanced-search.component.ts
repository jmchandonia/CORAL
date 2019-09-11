import { Component, OnInit } from '@angular/core';
import { Select2OptionData } from 'ng2-select2';
import { QueryBuilderService } from '../../shared/services/query-builder.service';
import { QueryBuilder, QueryParam, QueryMatch } from '../../shared/models/QueryBuilder';
import { Router, ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-advanced-search',
  templateUrl: './advanced-search.component.html',
  styleUrls: ['./advanced-search.component.css']
})
export class AdvancedSearchComponent implements OnInit {

  queryBuilderObject: QueryBuilder;
  showConnectionsUp = false;
  showConnectionsDown = false;
  showProcessesUp = false;
  showProcessesDown = false;
  operators;

  constructor(
    queryBuilder: QueryBuilderService,
    private router: Router,
    private route: ActivatedRoute,
    private http: HttpClient
  ) { }

  ngOnInit() {

    this.queryBuilderObject = this.queryBuilder.getCurrentObject();

    this.queryBuilder.getUpdatedObject().subscribe(object => {
      Object.assign(this.queryBuilderObject, object);
    });

    this.http.get('https://psnov1.lbl.gov:8082/generix/search_operations')
      .subscribe((data: any) => {
        this.operators = data.results;
      });
  }

  addProcess(process, queryParam) {
    this.queryBuilder.addProcessParam(process, queryParam);
  }

  updateProcess(process, index, queryParam) {
    this.queryBuilder.updateProcessParam(process, index, queryParam);
  }

  removeProcess(process, queryParam) {
    this.queryBuilder.removeProcessParam(process, queryParam);
  }

  onSubmit() {
    this.queryBuilder.submitSearchResults();
    this.router.navigate(['../result'], {relativeTo: this.route});
  }

  testQuery() {
    console.log('CURRENT QUERY', this.queryBuilderObject);
  }

}
