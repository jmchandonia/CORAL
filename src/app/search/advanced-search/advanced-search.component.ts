import { Component, OnInit, ChangeDetectorRef } from '@angular/core';
import { Select2OptionData } from 'ng2-select2';
import { QueryBuilderService } from '../../shared/services/query-builder.service';
import { QueryBuilder, QueryParam, QueryMatch } from '../../shared/models/QueryBuilder';
import { Router, ActivatedRoute } from '@angular/router';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-advanced-search',
  templateUrl: './advanced-search.component.html',
  styleUrls: ['./advanced-search.component.css'],
})
export class AdvancedSearchComponent implements OnInit {

  queryBuilderObject: QueryBuilder;
  showAdvancedFilters = false;
  operators;
  processes = [];
  public dataTypes;
  public dataModels;

  constructor(
    private queryBuilder: QueryBuilderService,
    private router: Router,
    private route: ActivatedRoute,
    private http: HttpClient,
    private chRef: ChangeDetectorRef
  ) { }

  ngOnInit() {

    this.queryBuilderObject = this.queryBuilder.getCurrentObject();

    this.getOperators();
    this.getDataModels();
    this.getDataTypes();

  }

  getOperators() {
    this.queryBuilder.getOperators()
      .subscribe((data: any) => {
        this.operators = data.results;
      });
  }

  getDataModels() {
    this.queryBuilder.getDataModels()
      .subscribe((data: any) => {
        this.dataModels = data.results;
        this.processes = this.dataModels.Process.properties;
      });
  }

  getDataTypes() {
    this.queryBuilder.getDataTypes()
      .subscribe((data: any) => {
        this.dataTypes = data.results;
      });
  }

  get dataProps() {
    const { operators, dataTypes, dataModels } = this;
    return { operators, dataTypes, dataModels };
  }

  addProcess(process, queryParam) {
    // this.queryBuilder.addProcessParam(process, queryParam);
    // this.queryBuilderObject.push()
  }

  updateProcess(process, index, queryParam) {
    // this.queryBuilder.updateProcessParam(process, index, queryParam);
  }

  removeProcessUp(index) {
    console.log('REMOVING PROCESSES UP');
    const { processesUp } = this.queryBuilderObject;
    this.queryBuilderObject.processesUp = processesUp.filter((_, i) => i !== index);
  }

  onSubmit() {
    // this.queryBuilder.submitSearchResults();
    this.router.navigate(['../result'], {relativeTo: this.route});
    this.queryBuilder.setSearchType('advanced');
  }

  addProcessUp() {
    this.queryBuilderObject.processesUp.push(new QueryParam());
  }

  testQuery() {
    this.queryBuilder.testQueryBuilder();
  }

}
