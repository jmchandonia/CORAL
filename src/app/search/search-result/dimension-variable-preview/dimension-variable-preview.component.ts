import { Component, OnInit } from '@angular/core';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { NgxSpinnerService } from 'ngx-spinner';

@Component({
  selector: 'app-dimension-variable-preview',
  templateUrl: './dimension-variable-preview.component.html',
  styleUrls: ['./dimension-variable-preview.component.css']
})
export class DimensionVariablePreviewComponent implements OnInit {

  constructor(
    private queryBuilder: QueryBuilderService,
    private spinner: NgxSpinnerService
  ) { }

  id: string;
  index: number;
  numberOfRows: number;
  data: any;

  ngOnInit() {
    this.spinner.show();
    this.queryBuilder.getDimensionVariableValues(this.id, this.index)
      .subscribe((data: any) => {
        this.spinner.hide();
        this.data = data.results;
        this.numberOfRows = this.data.size > this.data.max_row_count
          ? this.data.max_row_count
          : this.data.size;
      });
  }

}
