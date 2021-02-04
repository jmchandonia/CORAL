import { Component, OnInit, Output, EventEmitter, Input } from '@angular/core';
import { QueryParam } from 'src/app/shared/models/QueryBuilder';
import { Term } from 'src/app/shared/models/brick';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { BsDatepickerConfig } from 'ngx-bootstrap/datepicker';

@Component({
  selector: 'app-process-filter',
  templateUrl: './process-filter.component.html',
  styleUrls: ['./process-filter.component.css'],
})
export class ProcessFilterComponent implements OnInit {

  private _queryParams: QueryParam[];

  @Input() set queryParams(_queryParams: QueryParam[]) {
    this._queryParams = _queryParams;
    _queryParams.forEach(queryParam => {
      this[queryParam.attribute] = queryParam;
    });
  }

  get queryParams() { return this._queryParams }

  datePickerConfig: Partial<BsDatepickerConfig> = { containerClass: 'theme-dark-blue' };

  processes: Observable<Term[]>;
  campaigns: Observable<Term[]>;
  personnel: Observable<Term[]>;

  process: QueryParam;
  campaign: QueryParam;
  person: QueryParam;
  date_start: QueryParam;
  date_end: QueryParam;

  constructor(
    private queryBuilder: QueryBuilderService
  ) { }

  ngOnInit(): void {
    this.processes = this.queryBuilder.getProcessOterms().pipe(map((data: any) => data.results));
    this.campaigns = this.queryBuilder.getCampaignOterms().pipe(map((data: any) => data.results));
    this.personnel = this.queryBuilder.getPersonnelOterms().pipe(map((data: any) => data.results));
  }

  addFilter(event, attribute, operator) {
    if (event) {
      if (event.text) {
        this.queryParams.push(new QueryParam(attribute, '=', event.text, 'string'));
      } else {
        // input is a date, convert to yyyy-mm-dd
        const dateFormat = event.toISOString().split('T')[0];
        this.queryParams.push(new QueryParam(attribute, operator, dateFormat, 'string'));
      }
    } else {
      const idxToRemove = this.queryParams.indexOf(this.queryParams.find(x => x.attribute === attribute));
      this.queryParams.splice(idxToRemove, 1);
    }
  }

  reformat(date) {
    // reformat date for user input (if search object is coming from cache)
    const [year, month, day] = date.split('-');
    return `{${month}/${day}/${year}}`;
  }
}
