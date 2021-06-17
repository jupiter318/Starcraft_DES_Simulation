#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <set>

using namespace std;

void generate(int n, int flag, vector<int> im, int max, vector<vector<int>>& idx_vec) {
    if (n == 0) {
        /*for (auto i : im) {
            cout << i << " ";
        }
        cout << endl;*/
        idx_vec.push_back(im);
        return;
    }
    for (int i = flag+1; i < max; i++) {
        //cout << "n = " << n << "i = " << i << endl;
        im[im.size()-n] = i;
        generate(n - 1, i, im, max, idx_vec);
    }
}
bool check_sup(string str) {
    int count = 0;
    int sup_count = 0;
    for (int i = 0; i < str.length(); i++) {
        if (str[i] == 's' || str[i] == 'm') {
            count++;
        }
        else if (str[i] == 'u') {
            sup_count++;
        }

        if (count > sup_count * 8 + 10) {
            return false;
        }
    }
    return true;
}
int main()
{

    int command_num = 0;
    int barracks_num = 2;
    int marine_num = 8;
    int scv_num = 5;
    int sup_num = 1;
    vector<int> imsi;
    imsi.resize(barracks_num);

    //marine
    vector<vector<int>> marine_idx_vec;
    generate(barracks_num, -1, imsi, barracks_num+marine_num, marine_idx_vec);
    /*for (auto i : idx_vec) {
        for (auto j : i) {
            cout << j;
        }
        cout << endl;
    }*/
    //scv
    vector<vector<int>> scvidx_vec;
    imsi.clear();
    imsi.resize(scv_num);
    generate(scv_num, -1, imsi, barracks_num + marine_num+scv_num, scvidx_vec);

    //command
    vector<vector<int>> com_idx_vec;
    imsi.clear();
    imsi.resize(command_num);
    generate(command_num, -1, imsi, barracks_num + marine_num + scv_num + command_num, com_idx_vec);

    //supply
    vector<vector<int>> sup_idx_vec;
    imsi.clear();
    imsi.resize(sup_num);
    generate(sup_num, -1, imsi, barracks_num + marine_num + scv_num + command_num + sup_num, sup_idx_vec);

    ofstream fout("mar_bar.txt");

    vector<char> vec(marine_num, 'm');
    /*for (auto i : vec) {
        cout << i << " ";
    }*/
    for (int j = 0; j < marine_idx_vec.size(); j++) {
        vector<char> imvec = vec;
        //barracks
        if (marine_idx_vec[j][0] == 0) {
            for (int i = 0; i < marine_idx_vec[j].size(); i++) {
                imvec.insert(imvec.begin() + marine_idx_vec[j][i], 'b');
            }
        }
        else {
            break;
        }

        //print
        for (auto i : imvec) {
            fout << i;
        }
        fout << endl;
    }
    fout.close();

    //scv
    ofstream f1out("mbs.txt");
    ifstream fin("mar_bar.txt");
    string line;
    int count = 0;
    while (getline(fin, line))
    {
        count++;
        for (int i = 0; i < scvidx_vec.size(); i++) {
            string m_b_line = line;
            for (int j = 0; j < scvidx_vec[i].size(); j++) {
                m_b_line.insert(scvidx_vec[i][j], "s");
            }
            f1out << m_b_line << endl;
        }
        cout << "scv " <<count << " complete" << endl;

    }
    f1out.close();


    //command
    //ofstream f1out("mbs.txt");
    //ifstream fin("mar_bar.txt");
    //string line;
    //while (getline(fin, line))
    //{

    //    for (int i = 0; i < scvidx_vec.size(); i++) {
    //        string m_b_line = line;
    //        for (int j = 0; j < scvidx_vec[i].size(); j++) {
    //            m_b_line.insert(scvidx_vec[i][j], "s");
    //        }
    //        f1out << m_b_line << endl;
    //    }

    //}
    //f1out.close();

    //supply
    ofstream f2out("m"+ to_string(marine_num) + "b" + to_string(barracks_num) + "s" + to_string(scv_num) + "u" + to_string(sup_num) + ".txt");
    ifstream fin2("mbs.txt");
    count = 0;
    while (getline(fin2, line))
    {
        count++;
        for (int i = 0; i < sup_idx_vec.size(); i++) {
            string m_b_line = line;
            for (int j = 0; j < sup_idx_vec[i].size(); j++) {
                m_b_line.insert(sup_idx_vec[i][j], "u");
            }
            if (check_sup(m_b_line)) {
                f2out << m_b_line << endl;
            }

        }
        cout <<"supply " << count << " complete" << endl;

    }
    f2out.close();



    return 0;
}
