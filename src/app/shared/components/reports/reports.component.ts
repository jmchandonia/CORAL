import { Component, OnInit } from '@angular/core';
import { HomeService } from 'src/app/shared/services/home.service';

@Component({
  selector: 'app-reports',
  templateUrl: './reports.component.html',
  styleUrls: ['./reports.component.css']
})
export class ReportsComponent implements OnInit {

  constructor(private homeService: HomeService) { }

  reportsData: Array<{id: string, name: string}> = [];
  dataTable: any;
  selectedValue: any;

  ngOnInit() {
    this.homeService.getReports().subscribe((data: any) => {
      this.reportsData = [...data.results];
    });
    }

  updateTable(event) {
    this.homeService.getReportItem(event.id).subscribe((res: any) => {
      if (res.status === 'OK') {
        this.selectedValue = JSON.parse(res.results);
      }
    });
  }
}
