import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { SearchResultComponent } from './search-result.component';
import { RouterModule } from '@angular/router';
import { NgxSpinnerModule } from 'ngx-spinner';
import { HttpClientModule } from '@angular/common/http';

describe('SearchResultComponent', () => {

  let spectator: Spectator<SearchResultComponent>
  const createComponent = createComponentFactory({
    component: SearchResultComponent,
    imports: [
      RouterModule.forRoot([]),
      NgxSpinnerModule,
      HttpClientModule
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
