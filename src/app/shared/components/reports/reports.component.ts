import { Component, OnInit } from '@angular/core';
import 'datatables.net';
import 'datatables.net-bs4';
import * as $ from 'jquery';
import { HttpClient } from '@angular/common/http';
import { environment } from 'src/environments/environment';

@Component({
  selector: 'app-reports',
  templateUrl: './reports.component.html',
  styleUrls: ['./reports.component.css']
})
export class ReportsComponent implements OnInit {

  constructor(private http: HttpClient) { }

  select2Data: any = [
    {id: '', text: ''},
  ];

  public ajax: Select2AjaxOptions;
  options: Select2Options = {
    width: '100%',
    placeholder: 'Browse By Type',
    containerCssClass: 'select2-custom-container'
  };
  browseItems: any[];
  dataTable: any;
  selectedValue: any;

  ngOnInit() {
    this.ajax = {
      url: `${environment.baseURL}/reports`,
      dataType: 'json',
      delay: 250,
      cache: false,
      processResults: (data: any) => {
        this.browseItems = data.results;
        return {
          results: $.map(data.results, obj => {
            return {id: obj.id, text: obj.name};
          }),
        };
      },
    };
    this.options.ajax = this.ajax;
    const table: any = $('table');
    this.dataTable = table.DataTable();
    }

    updateTable(event) {
      this.http.get(`${environment.baseURL}/reports/${event.value}`)
      .subscribe((res: any) => {
        if (res.status === 'OK') {
          this.selectedValue = JSON.parse(res.results);
        }
      });
    }
}
